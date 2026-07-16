import streamlit as st
from model_util import predict_msg, find_spam_words, highlight_words,advanced_url_analysis

tab1, tab2 = st.tabs(["Spam Detection", "URL Checker"])
    
with tab1:
    st.markdown('<div class="big-title">Spam Shield</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">AI-Based Message & URL Security System</div>', unsafe_allow_html=True)
    st.divider()
    st.write("Check whether a message is Spam or Not")

    st.set_page_config(
    page_title="Spam Shield",
    layout="centered"
    )
    user_input = st.text_area("Enter SMS or Email:", height=150)
    if st.button("Analyze Message"):
        if user_input.strip() == "":
            st.warning("Please enter some text")
        else:
            result,prob = predict_msg(user_input)
            confidence = round(prob * 100, 2)
        # st.write(predict_msg(user_input))
            if result == "spam":
                st.error("Alert SPAM message detected")
            else:
                st.success("This message is NOT spam")
            st.write("Spam Probability:", confidence, "%")
            suspicious = find_spam_words(user_input)
            highlighted_text = highlight_words(user_input, suspicious)
            st.markdown(f"### Analyzed Message:\n\n{highlighted_text}",unsafe_allow_html=True)

            st.divider()
            st.subheader("File Scanner")
            uploaded_file = st.file_uploader("Upload .txt or .csv file",type=["txt", "csv"])

            if uploaded_file is not None:
                if uploaded_file.name.endswith(".txt"):
                    content = uploaded_file.read().decode("utf-8")
                    messages = content.split("\n")

                elif uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                    messages = df.iloc[:, 0].dropna().tolist()

                results = []

                for msg in messages:
                    pred, prob = predict_msg(msg)
                    results.append({
                        "Message": msg[:50],
                        "Prediction": pred,
                        "Spam Probability (%)": round(prob * 100, 2)
                })

                result_df = pd.DataFrame(results)

                st.write("### Results:")
                st.dataframe(result_df)

                spam_count = sum(1 for r in results if r["Prediction"] == "spam")
                total = len(results)

                st.write("### Summary")
                st.write(f"Total Messages: {total}")
                st.write(f"Spam Detected: {spam_count}")

with tab2:
    st.header("Check URL Safety")

    url_input = st.text_input("Enter URL")

    if "url_result" not in st.session_state:
        st.session_state.url_result = None

    if "show_details" not in st.session_state:
        st.session_state.show_details = False
    if st.button("Scan URL"):
        if url_input.strip() == "":
            st.warning("Please enter a URL")
        else:
            result = advanced_url_analysis(url_input)

            # Save result in session
            st.session_state.url_result = result
            st.session_state.show_details = False

    # -------- SHOW STATUS --------
    if st.session_state.url_result:
        status = st.session_state.url_result["status"]

        if status == "HIGH RISK":
            st.error("🚨 HIGH RISK URL")
        elif status == "SUSPICIOUS":
            st.warning("⚠️ Suspicious URL")
        else:
            st.success("✅ Safe URL")

        # -------- SECOND BUTTON --------
        if st.button("Show Detailed Analysis"):
            st.session_state.show_details = True

    # -------- SHOW DETAILS --------
    if st.session_state.show_details and st.session_state.url_result:
        result = st.session_state.url_result

        st.write("### 🔍 URL Details")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Domain:**", result["domain"])
            st.write("**IP Address:**", result["ip"])

        with col2:
            st.write("**Risk Score:**", result["risk_score"])
            st.progress(result["risk_score"])

        st.write("### Reasons:")
        for r in result["reasons"]:
            st.write("•", r)    
    