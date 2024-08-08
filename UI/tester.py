import streamlit as st

# Set the page configuration
st.set_page_config(layout="wide")

# Title of the dashboard
st.title("Account Intelligence Dashboard")

# Read and apply custom CSS
with open("design.css") as source:
    st.markdown(f"<style>{source.read()}</style>", unsafe_allow_html=True)

# Load LLM output from file
with open("newsOutput.md", "r") as file:
    llm_output_news = file.read()

with open("jobsOutput.md", "r") as file:
    llm_output_jobs = file.read()


# Create the main layout with columns
main_col, chat_col = st.columns([3, 1])

with main_col:
    # Create two columns for the four boxes
    col1, col2 = st.columns(2)

    with col1:
        st.header("News Insight")
        st.markdown(f"<div class='stScrollable'>{llm_output_news}</div>", unsafe_allow_html=True)

    with col2:
        st.header("Jobs Insight")
        st.markdown(f"<div class='stScrollable'>{llm_output_jobs}</div>", unsafe_allow_html=True)

    # Add a spacer
    st.markdown("<div class='stContainer'></div>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        st.header("Yahoo Finance")
        st.write("Yahoo Finance content goes here")

    with col4:
        st.header("CRM Insights")
        st.write("CRM Insights content goes here")

with chat_col:
    # Chat window
    st.header("Chat Window")
    st.write("Chat content goes here")
    st.text_area("Chat", height=400)
