import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Title
st.title('Simple Streamlit App')

# Data
data = pd.DataFrame({
    'x': np.random.randn(100),
    'y': np.random.randn(100)
})

# Plot
st.line_chart(data)

# Text
st.write('Hello, this is a simple Streamlit app!')
