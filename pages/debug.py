import streamlit as st
import pandas as pd

st.title("データファイル読み込みテスト")

# 存在しないファイルを読み込もうとする
try:
    df = pd.read_csv("missing_data.csv")
    st.dataframe(df)
except Exception as e:
    st.error(f"エラーが発生しました: {e}")