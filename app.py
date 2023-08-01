import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
import streamlit.components.v1 as components
import time
import base64

# Function to generate a download link
def generate_download_link(df, filename):
    csv = df.to_html(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

def parse_command(cmd):
    cmd_parts = cmd.split(" ")
    cmd_dict = {}

    for part in cmd_parts:
        if "=" in part:
            key, value = part.split("=", 1)
            cmd_dict[key] = value
    return cmd_dict

def align_keys(cmd1_dict, cmd2_dict):
    aligned_keys = []

    for key1 in cmd1_dict.keys():
        for key2 in cmd2_dict.keys():
            # Only consider keys that have not been aligned yet and have a high similarity score
            if key2 not in [x[1] for x in aligned_keys] and fuzz.ratio(key1, key2) > 80:
                aligned_keys.append((key1, key2))

    # Return aligned keys and remaining unaligned keys
    return aligned_keys, cmd1_dict.keys() - [x[0] for x in aligned_keys], cmd2_dict.keys() - [x[1] for x in aligned_keys]

def compare_commands(cmd1, cmd2):
    cmd1_dict = parse_command(cmd1)
    cmd2_dict = parse_command(cmd2)

    aligned_keys, only_in_cmd1, only_in_cmd2 = align_keys(cmd1_dict, cmd2_dict)

    comparison_result_same = []
    comparison_result_similar = []
    comparison_result_different = []

    # Check keys only in cmd1
    for key in sorted(only_in_cmd1):
        comparison_result_different.append([key, cmd1_dict[key], None, 'Mismatch'])

    # Check keys only in cmd2
    for key in sorted(only_in_cmd2):
        comparison_result_different.append([key, None, cmd2_dict[key], 'Mismatch'])

    # Check aligned keys
    for key1, key2 in sorted(aligned_keys):
        if cmd1_dict[key1] == cmd2_dict[key2]:
            comparison_result_same.append([f"{key1} ~ {key2}", cmd1_dict[key1], cmd2_dict[key2], 'Match'])
        else:
            comparison_result_similar.append([f"{key1} ~ {key2}", cmd1_dict[key1], cmd2_dict[key2], 'Mismatch'])

    return comparison_result_same, comparison_result_similar, comparison_result_different

def color_status(val):
    if val == 'Mismatch':
        color = 'red'
    else:
        color = 'green'
    return f'color: {color}'

# Streamlit code
st.title("Command Comparison Tool")

# Enter command with help message
with st.expander("Help", False):
    st.write("For more details, check: https://github.com/krai/axs2qaic-dev/issues/70")

cmd1 = st.text_area("Enter CK command:", "")
cmd2 = st.text_area("Enter AXS command:", "")

def escape_markdown(text):
    return text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t").replace("'", "\\'")

def get_table_download_link():
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    stamp = time.strftime("%Y%m%d-%H%M%S")
    html = f'<a href="report_{stamp}.html" download="report_{stamp}.html">Click here to download the report</a>'
    with open(f'report_{stamp}.html', 'w') as f:
        f.write(html)
    return html

if st.button("Compare"):
    result_same, result_similar, result_different = compare_commands(cmd1, cmd2)
    df_same = pd.DataFrame(result_same, columns=['Key', 'CK Value', 'AXS Value', 'Status']).sort_values(by=['Key'])
    df_similar = pd.DataFrame(result_similar, columns=['Key', 'CK Value', 'AXS Value', 'Status']).sort_values(by=['Key'])
    df_different = pd.DataFrame(result_different, columns=['Key', 'CK Value', 'AXS Value', 'Status']).sort_values(by=['Key'])

    st.subheader("Same Parameters")
    st.write(df_same.style.applymap(color_status, subset=['Status']))
    with st.expander("Copy Same Parameters Table", False):
        st.code(df_same.to_markdown())

    st.subheader("Similar Parameters")
    st.write(df_similar.style.applymap(color_status, subset=['Status']))
    with st.expander("Copy Similar Parameters Table", False):
        st.code(df_similar.to_markdown())

    st.subheader("Different Parameters")
    st.write(df_different.style.applymap(color_status, subset=['Status']))
    with st.expander("Copy Different Parameters Table", False):
        st.code(df_different.to_markdown())

    st.subheader("More info")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("Parameters from CK Command")
        st.table(pd.DataFrame(parse_command(cmd1).items(), columns=['Key', 'Value']).sort_values(by=['Key']))

    with col2:
        st.markdown("Parameters from AXS Command")
        st.table(pd.DataFrame(parse_command(cmd2).items(), columns=['Key', 'Value']).sort_values(by=['Key'])) s