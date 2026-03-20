import batchalign as ba
from tqdm import tqdm
import os
import pandas as pd
import stanza
from pprint import pprint
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor

stanza.download("en")

raw_train_news_df = pd.read_csv("F:/NT@B/Microsoft-sp26/MINDlarge_train/news.tsv", sep="\t")
raw_test_news_df = pd.read_csv("F:/NT@B/Microsoft-sp26/MINDlarge_test/news.tsv", sep="\t")

header_data = ["id", "category", "subcategory", "title", "abstract", "url", "title_entities", "abstract_entities"]
raw_train_news_df.columns = header_data
raw_test_news_df.columns = header_data

train_news_df = raw_train_news_df[raw_train_news_df["category"] == "news"]
test_news_df = raw_test_news_df[raw_test_news_df["category"] == "news"]

train_news_df = train_news_df.reset_index(drop=True)
test_news_df = test_news_df.reset_index(drop=True)

train_news_df = train_news_df[~train_news_df["abstract"].isna()]
test_news_df = test_news_df[~test_news_df["abstract"].isna()]

test_news_df = test_news_df[~test_news_df["id"].isin(train_news_df["id"])]
test_news_df = test_news_df.reset_index(drop=True)

CLAUSAL_DEPRELS = {"ccomp", "xcomp", "advcl", "acl", "acl:relcl", "parataxis"}
SENT_LABELS = {"S", "SBAR", "SBARQ", "SINV", "SQ"}
PUNCT_TAGS = {".", ",", ":", "``", "''", "-LRB-", "-RRB-", "#", "$"}

def clause_count_from_dependencies(stanza_sentence):
    count = 0

    # main clause: one root predicate
    root_words = [w for w in stanza_sentence.words if w.head == 0]
    if root_words:
        count += 1

    # embedded/subordinate clauses
    for w in stanza_sentence.words:
        if w.deprel in CLAUSAL_DEPRELS:
            count += 1

    return count

def clause_density(stanza_doc):
    densities = []
    for sent in stanza_doc.sentences:
        n_clauses = clause_count_from_dependencies(sent)
        densities.append(n_clauses)  # per sentence
    return densities

def dependency_lengths(stanza_sentence):
    dists = []
    for w in stanza_sentence.words:
        if w.head != 0:  # skip root
            dists.append(abs(w.id - w.head))
    return dists

def mean_dependency_length(stanza_doc):
    dist_per_sentence = []
    for sent in stanza_doc.sentences:
        dists = dependency_lengths(sent)
        dist_per_sentence.append(sum(dists) / len(dists) if dists else 0.0)
    return dist_per_sentence

def is_leaf(node) -> bool:
    return len(node.children) == 0

def is_preterminal(node) -> bool:
    return len(node.children) == 1 and is_leaf(node.children[0])

def is_punct_preterminal(node) -> bool:
    return is_preterminal(node) and node.label in PUNCT_TAGS

def leaf_text(node) -> str:
    return node.label

def iter_leaf_paths(node, path=None):
    """
    Yield tuples: (leaf_node, path)
    where path is a list of (parent_node, child_index) from root down to the leaf.
    """
    if path is None:
        path = []

    if is_leaf(node):
        yield node, path
        return

    for i, child in enumerate(node.children):
        yield from iter_leaf_paths(child, path + [(node, i)])

def iter_nodes(node):
    yield node
    for child in node.children:
        yield from iter_nodes(child)

def count_non_punct_words(tree) -> int:
    count = 0
    for node in iter_nodes(tree):
        if is_preterminal(node) and not is_punct_preterminal(node):
            count += 1
    return count

def left_embedding_depth(tree) -> int:
    """
    Constituency-based operationalization:
    For each leaf path, count how many ancestors keep the leaf on the left edge
    of an unfinished constituent, i.e. the child is the first child and the parent
    has material to the right.

    Sentence score = maximum such depth across leaves.
    """
    max_depth = 0

    for leaf, path in iter_leaf_paths(tree):
        depth = 0
        for parent, child_idx in path:
            if is_preterminal(parent):
                continue
            if child_idx == 0 and len(parent.children) > 1:
                depth += 1
        max_depth = max(max_depth, depth)

    return max_depth

def center_embedding_depth(tree) -> int:
    """
    Constituency-based operationalization:
    Count nested sentential constituents (S, SBAR, SBARQ, SINV, SQ)
    that occur in a non-final position of another sentential constituent.

    This captures center-embedding rather than simple right-branching.
    """
    def helper(node, active_center_depth=0):
        best = active_center_depth

        for i, child in enumerate(node.children):
            child_depth = active_center_depth

            if child.label in SENT_LABELS and not is_preterminal(child):
                # Embedded clause inside a non-final position -> center embedding increment
                if i < len(node.children) - 1:
                    child_depth += 1

            best = max(best, helper(child, child_depth))

        return best

    return helper(tree, 0)

def yngve_scores(tree) -> Dict[str, Any]:
    """
    For each leaf:
      score = sum over ancestors of the number of right siblings.
    Returns per-word scores plus sum/mean/max over words.
    """
    per_word = []

    for leaf, path in iter_leaf_paths(tree):
        # Ignore punctuation leaves by checking their preterminal parent
        if len(path) >= 1:
            parent, _ = path[-1]
            if is_punct_preterminal(parent):
                continue

        score = 0
        for parent, child_idx in path:
            score += (len(parent.children) - child_idx - 1)

        per_word.append({
            "word": leaf_text(leaf),
            "score": score
        })

    values = [x["score"] for x in per_word]
    return {
        "per_word": per_word,
        "sum": sum(values),
        "mean": (sum(values) / len(values)) if values else 0.0,
        "max": max(values) if values else 0
    }

def frazier_scores(tree) -> Dict[str, Any]:
    """
    A compact, reproducible Frazier-style implementation.

    For each leaf:
      - climb from the POS preterminal upward
      - only count nodes while the current node remains the leftmost child
        of its parent (once there is a left sibling, stop)
      - add:
          1.5 for sentence-level nodes: S, SBAR, SBARQ, SINV, SQ
          1.0 for other phrasal nonterminals
      - ignore the POS preterminal itself and punctuation

    This is a practical approximation; exact conventions vary across papers.
    """
    per_word = []

    for leaf, path in iter_leaf_paths(tree):
        if not path:
            continue

        preterminal, _ = path[-1]
        if is_punct_preterminal(preterminal):
            continue

        score = 0.0

        # path is [(root, idx), ..., (preterminal, idx_of_leaf)]
        # We score ancestors from the preterminal's parent upward.
        # Stop once the current node is not the leftmost child of its parent.
        # Current "node" starts as the preterminal.
        for level in range(len(path) - 2, -1, -1):
            parent, child_idx = path[level]

            # Count this parent node
            if parent.label in SENT_LABELS:
                score += 1.5
            else:
                score += 1.0

            # If this parent itself is not leftmost in its own parent, stop
            if level > 0:
                _, parent_idx_in_grandparent = path[level - 1]
                if parent_idx_in_grandparent != 0:
                    break

        per_word.append({
            "word": leaf_text(leaf),
            "score": score
        })

    values = [x["score"] for x in per_word]
    return {
        "per_word": per_word,
        "sum": sum(values),
        "mean": (sum(values) / len(values)) if values else 0.0,
        "max": max(values) if values else 0.0
    }

def analyze_doc(doc, surprisal_model: Optional[Any] = None) -> Dict[str, Dict[str, Any]]:
    """
    doc = stanza_pipeline(text)

    Returns one dict per sentence.
    """
    rows = {}

    for i, sent in enumerate(doc.sentences):
        tree = sent.constituency

        row = {
            # "sentence_text": sent.text,
            "n_words": count_non_punct_words(tree),
            "left_embedding_depth": left_embedding_depth(tree),
            "center_embedding_depth": center_embedding_depth(tree),
        }

        yngve = yngve_scores(tree)
        row["yngve_sum"] = yngve["sum"]
        row["yngve_mean"] = yngve["mean"]
        row["yngve_max"] = yngve["max"]
        #row["yngve_per_word"] = yngve["per_word"]

        frazier = frazier_scores(tree)
        row["frazier_sum"] = frazier["sum"]
        row["frazier_mean"] = frazier["mean"]
        row["frazier_max"] = frazier["max"]
        #row["frazier_per_word"] = frazier["per_word"]

        if surprisal_model is not None:
            s = surprisal_model.sentence_surprisal_summary(sent.text)
            row["surprisal_sum"] = s["sum"]
            row["surprisal_mean"] = s["mean"]
            row["surprisal_max"] = s["max"]
            row["surprisal_per_token"] = s["per_token"]

        rows[f"Sentence {i+1}"] = row

    return rows

# One set of heavy models per worker process
_worker_stanza_pipeline = None

def init_worker():
    global _worker_stanza_pipeline

    _worker_stanza_pipeline = stanza.Pipeline(
        lang="en",
        processors="tokenize,mwt,pos,lemma,depparse,constituency",
        download_method=None  # type: ignore 
        # Don't try to download models in each worker
    )

def process_abstract(task: Tuple[Any, str]) -> Tuple[Any, Dict[str, Any]]:
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    global _worker_stanza_pipeline

    if _worker_stanza_pipeline is None:
        init_worker()

    abstract_id, abstract = task

    if pd.isna(abstract) or not str(abstract).strip():
        return abstract_id, {
            "Number of Sentences": 0,
            "Mean Sentence Length (characters)": 0,
            "Density of Clauses": 0,
            "Mean Dependency Length": 0,
            "sentence_features": {}
        }

    abstract = str(abstract)

    # Stanza parse
    stanza_doc = _worker_stanza_pipeline(abstract) # type: ignore

    # Sentence-level features from your function
    sentence_features = analyze_doc(stanza_doc)

    result = {
        "Number of Sentences": len(stanza_doc.sentences), # type: ignore
        "Mean Sentence Length (characters)": (
            sum(len(s.tokens) for s in stanza_doc.sentences) / len(stanza_doc.sentences) if len(stanza_doc.sentences) > 0 else 0 # type: ignore
        ),
        "Density of Clauses": clause_density(stanza_doc),
        "Mean Dependency Length": mean_dependency_length(stanza_doc),
        "sentence_features": sentence_features
    }

    return abstract_id, result

def parallel_extract_features(news_df: pd.DataFrame, max_workers: int = None) -> Dict[Any, Dict[str, Any]]: # type: ignore
    if max_workers is None:
        max_workers = max(1, os.cpu_count() - 1)
        print(f"Using {max_workers} worker processes for parallel feature extraction.")

    tasks = list(zip(news_df.iloc[:, 0], news_df["abstract"]))
    features = {}

    with ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=init_worker
    ) as executor:
        results = executor.map(process_abstract, tasks, chunksize=1)

        for abstract_id, feature_dict in tqdm(results, total=len(tasks)):
            features[abstract_id] = feature_dict

    return features

if __name__ == "__main__":
    import json
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import multiprocessing
    multiprocessing.freeze_support()
    features = parallel_extract_features(test_news_df[:50], max_workers=2)
    json.dump(features, open("small_test_features.json", "w"), indent=2)
    # pprint(features['N47214'])