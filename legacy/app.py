import streamlit as st

st.set_page_config(page_title='Indy Explorer', page_icon='⛷️')

st.markdown(
    '<style>h1, .stMarkdown p { text-align: center; }</style>',
    unsafe_allow_html=True,
)

st.title('Indy Explorer has Moved!')
st.markdown(
    'The app now lives at **[indy-explorer.vercel.app](https://indy-explorer.vercel.app)** '
    '— please update your bookmark.'
)
st.markdown(
    'The new app loads instantly — no more waiting for the server to wake up. '
    'It also has everything the old one did, plus filters for blackout dates, '
    'Peak Rankings scores, reservation requirements, and more.'
)
_, col, _ = st.columns([1, 1, 1])
with col:
    st.link_button(
        '⛷️ Go to Indy Explorer',
        'https://indy-explorer.vercel.app',
        type='primary',
        use_container_width=True,
    )
