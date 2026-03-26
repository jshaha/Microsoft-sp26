import streamlit as st
import html
import streamlit.components.v1 as components
import collections
import pandas as pd
from pprint import pprint

articles = pd.read_csv("./MINDlarge_train/news.tsv", sep="\t")
articles.columns = ["id", "category", "subcategory", "title", "abstract", "url", "title_entities", "abstract_entities"]
articles = articles[articles['abstract'].notna()]
category_dfs = {}
for category in set(articles['category']):
    category_dfs[category] = articles[articles['category'] == category][:3]

entity_affect = pd.read_json("entity_affect_val_normalized.jsonl", lines=True)
pprint(len(entity_affect['entities'].iloc[0]))

# st.set_page_config(page_title="CLAN Use Ideation", layout="wide")

# st.title("CLAN Use Ideation")

# st.markdown("""
#     <style>
#         .scroll-box {
#             height: 400px;
#             overflow-y: auto;
#             padding: 12px;
#             border: 1px solid #d0d0d0;
#             border-radius: 10px;
#             background-color: #f8f9fa;
#             color: black;
#         }

#         .scroll-item {
#             border: 2px solid black;
#             border-radius: 6px;
#             padding: 8px;
#             margin-bottom: 8px;
#             background-color: white;
#         }

#         .item-title {
#             font-weight: bold;
#             margin-bottom: 4px;
#             word-wrap: break-word;
#         }

#         .item-abstract {
#             color: #555;
#             font-size: 0.9em;
#         }
#     </style>""", 
# unsafe_allow_html=True)

# col1, col2, col3, col4 = st.columns(4)

def render_chip_column(items, header, key):
    html_content = f"""
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: white;
        }}

        .header {{
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .scroll-box {{
            height: 500px;
            overflow-y: auto;
            padding: 6px;
            background-color: #f8f9fa;
            border: 1px solid #ccc;
            border-radius: 8px;
        }}

        .scroll-item {{
            position: relative;
            border: 2px solid black;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
            background-color: white;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}

        .scroll-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }}

        .item-title {{
            font-weight: bold;
            margin-bottom: 8px;
            word-wrap: break-word;
            line-height: 1.3;
        }}

        .entities {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}

        .entity-chip {{
            display: inline-block;
            padding: 4px 8px;
            border: 1px solid black;
            border-radius: 999px;
            font-size: 12px;
            background: #f2f2f2;
            white-space: nowrap;
        }}

        .entity-text {{
            font-weight: bold;
        }}

        .entity-type {{
            color: #444;
            margin-left: 4px;
        }}

        .tooltip {{
            visibility: hidden;
            opacity: 0;
            transition: opacity 0.15s ease;
            position: absolute;
            left: 10px;
            right: 10px;
            top: 100%;
            margin-top: 8px;
            z-index: 1000;
            background: black;
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-size: 13px;
            line-height: 1.4;
            text-align: left;
            box-shadow: 0 6px 16px rgba(0,0,0,0.25);
        }}

        .scroll-item:hover .tooltip {{
            visibility: visible;
            opacity: 1;
        }}
    </style>
    </head>
    <body>
        <div class="header">{html.escape(header)}</div>
        <div class="scroll-box">
    """

    for i, item in enumerate(items):
        title = html.escape(item["title"])
        abstract = html.escape(item["abstract"])

        entities = item.get("entities", [])
        entity_html = ""

        for ent in entities:
            ent_text = html.escape(str(ent.get("text", "")))
            ent_type = html.escape(str(ent.get("type", "")))
            ent_sentiment = html.escape(str(ent.get("sentiment", "")))

            chip_label = f"""
                <span class="entity-chip" title="type: {ent_type}, sentiment: {ent_sentiment}, evidence: {html.escape(str(ent.get('evidence', '')))}">
                    <span class="entity-text">{ent_text}</span>
                </span>
                """
            entity_html += chip_label

        html_content += f"""
        <div class="scroll-item">
            <div class="item-title">{title}</div>
            <div class="entities">{entity_html}</div>
            <div class="tooltip">{abstract}</div>
        </div>
        """

    html_content += """
        </div>
    </body>
    </html>
    """

    components.html(html_content, height=560, scrolling=False)

# def render_column(items, header, key):
#     html_content = f"""
#     <html>
#     <head>
#     <style>
#         body {{
#             margin: 0;
#             font-family: Arial, sans-serif;
#         }}

#         .header {{
#             font-size: 20px;
#             font-weight: bold;
#             margin-bottom: 10px;
#         }}

#         .scroll-box {{
#             height: 450px;
#             overflow-y: auto;
#             padding: 6px;
#             background-color: #f8f9fa;
#             border: 1px solid #ccc;
#             border-radius: 8px;
#         }}

#         .scroll-item {{
#             border: 2px solid black;
#             border-radius: 8px;
#             padding: 10px;
#             margin-bottom: 10px;
#             background-color: white;
#             cursor: pointer;
#             transition: transform 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease;
#         }}

#         .scroll-item:hover {{
#             transform: translateY(-2px);
#             box-shadow: 0 4px 10px rgba(0,0,0,0.15);
#             background-color: #f3f3f3;
#         }}

#         .item-title {{
#             font-weight: bold;
#             margin-bottom: 6px;
#             word-wrap: break-word;
#         }}

#         .item-abstract {{
#             color: #555;
#             font-size: 0.92em;
#         }}

#         .item-full-abstract {{
#             display: none;
#             margin-top: 8px;
#             color: #222;
#             font-size: 0.92em;
#             border-top: 1px solid #ddd;
#             padding-top: 8px;
#             word-wrap: break-word;
#         }}
#     </style>
#     <script>
#         function toggleAbstract(id) {{
#             const el = document.getElementById(id);
#             if (el.style.display === "block") {{
#                 el.style.display = "none";
#             }} else {{
#                 el.style.display = "block";
#             }}
#         }}
#     </script>
#     </head>
#     <body>
#         <div class="header">{html.escape(header)}</div>
#         <div class="scroll-box">
#     """

#     for i, item in enumerate(items.loc[:, ['title', 'abstract']].values):
#         # print(item)
#         title = html.escape(item[0])
#         abstract = html.escape(item[1])
#         preview = abstract[:20] + "..." if len(abstract) > 20 else abstract

#         html_content += f"""
#         <div class='scroll-item' onclick="toggleAbstract('{key}-abstract-{i}')">
#             <div class='item-title'>{title}</div>
#             <div class='item-abstract'>{preview}</div>
#             <div class='item-full-abstract' id='{key}-abstract-{i}'>{abstract}</div>
#         </div>
#         """

#     html_content += """
#         </div>
#     </body>
#     </html>
#     """

#     components.html(html_content, height=520, scrolling=False)

# categories = collections.deque(["Finance", "Entertainment", "News", "Sports"])

# # category = categories.popleft().lower()
# # for i, item in enumerate(category_dfs[category].loc[:, ['title', 'abstract']].values):
# #     print(i, item[0], item[1])
# # print(category_dfs[category]['title'].iloc[1] + " - " + category_dfs[category]['abstract'].iloc[1])

# with col1:
#     category = categories.popleft()
#     st.subheader(f"{category}")
#     #print(category_dfs[category.lower()]['title'].iloc[1] + " - " + category_dfs[category.lower()]['abstract'].iloc[1])
#     render_column(category_dfs[category.lower()], category, "col1")

# with col2:
#     category = categories.popleft()
#     st.subheader(f"{category}")
#     render_column(category_dfs[category.lower()], category, "col2")

# with col3:
#     category = categories.popleft()
#     st.subheader(f"{category}")
#     render_column(category_dfs[category.lower()], category, "col3")

# with col4:
#     category = categories.popleft()
#     st.subheader(f"{category}")
#     render_column(category_dfs[category.lower()], category, "col4")
