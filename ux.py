import streamlit as st
import collections
import pandas as pd

articles = pd.read_csv("./MINDlarge_train/news.tsv", sep="\t")
articles.columns = ["id", "category", "subcategory", "title", "abstract", "url", "title_entities", "abstract_entities"]
articles = articles[articles['abstract'].notna()]
category_dfs = {}
for category in set(articles['category']):
    category_dfs[category] = articles[articles['category'] == category]

st.set_page_config(page_title="CLAN Use Ideation", layout="wide")

st.title("CLAN Use Ideation")

st.markdown("""
    <style>
        .scroll-box {
            height: 400px;
            overflow-y: auto;
            padding: 12px;
            border: 1px solid #d0d0d0;
            border-radius: 10px;
            background-color: #f8f9fa;
            color: black;
        }

        .scroll-item {
            border: 2px solid black;
            border-radius: 6px;
            padding: 8px;
            margin-bottom: 8px;
            background-color: white;
        }

        .item-title {
            font-weight: bold;
            margin-bottom: 4px;
            word-wrap: break-word;
        }

        .item-abstract {
            color: #555;
            font-size: 0.9em;
        }
    </style>""", 
unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

def render_scroll_box(items):
    html = "<div class='scroll-box'>"
    for title, abstract in zip(items['title'], items['abstract']):
        html += f"""
          <div class='scroll-item'>
              <div class='item-title'>{title}</div>
              <div class='item-abstract'>{abstract[:20] + "..." if len(abstract) > 20 else abstract}</div>
          </div>
        """
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

categories = collections.deque(["Finance", "Entertainment", "News", "Sports"])

# category = categories.popleft().lower()
# print(category_dfs[category]['title'].iloc[1] + " - " + category_dfs[category]['abstract'].iloc[1])

with col1:
    category = categories.popleft()
    st.subheader(f"{category}")
    render_scroll_box(category_dfs[category.lower()])

with col2:
    category = categories.popleft()
    st.subheader(f"{category}")
    render_scroll_box(category_dfs[category.lower()])

with col3:
    category = categories.popleft()
    st.subheader(f"{category}")
    render_scroll_box(category_dfs[category.lower()])

with col4:
    category = categories.popleft()
    st.subheader(f"{category}")
    render_scroll_box(category_dfs[category.lower()])
