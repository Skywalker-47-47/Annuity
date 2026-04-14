import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

def calculate_amortization(principal, annual_rate, years):
    monthly_rate = annual_rate / 12 / 100
    months = years * 12
    
    if monthly_rate > 0:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
    else:
        monthly_payment = principal / months
    
    schedule = []
    balance = principal
    
    for month in range(1, months + 1):
        interest_payment = balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        balance -= principal_payment
        
        schedule.append({
            'Month': month,
            'Payment': round(monthly_payment, 2),
            'Principal': round(principal_payment, 2),
            'Interest': round(interest_payment, 2),
            'Balance': round(max(balance, 0), 2)
        })
    
    total_payment = monthly_payment * months
    total_interest = total_payment - principal
    
    return monthly_payment, total_interest, total_payment, pd.DataFrame(schedule)

def main():
    st.title("🏦 AI Amortization Calculator")
    st.markdown("Upload an Excel file or enter loan details manually")
    
    tab1, tab2 = st.tabs(["📁 Upload Excel", "⌨️ Manual Input"])
    
    with tab1:
        uploaded_file = st.file_uploader("Upload Excel file with loan data", type=['xlsx', 'xls'])
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("### Uploaded Data:")
                st.dataframe(df)
                
                required_cols = ['Principal', 'Annual_Rate', 'Years']
                if all(col in df.columns for col in required_cols):
                    for idx, row in df.iterrows():
                        principal = row['Principal']
                        annual_rate = row['Annual_Rate']
                        years = row['Years']
                        
                        monthly_payment, total_interest, total_payment, schedule = calculate_amortization(
                            principal, annual_rate, years
                        )
                        
                        st.write(f"#### Loan {idx + 1}: ${principal:,.2f} at {annual_rate}% for {years} years")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Monthly Payment", f"${monthly_payment:,.2f}")
                        col2.metric("Total Interest", f"${total_interest:,.2f}")
                        col3.metric("Total Payment", f"${total_payment:,.2f}")
                        
                        st.write("##### Amortization Schedule")
                        st.dataframe(schedule, use_container_width=True)
                else:
                    st.error(f"Excel file must contain columns: {required_cols}")
            except Exception as e:
                st.error(f"Error reading Excel file: {e}")
    
    with tab2:
        col1, col2, col3 = st.columns(3)
        with col1:
            principal = st.number_input("Principal Amount ($)", min_value=0.0, value=100000.0, step=1000.0)
        with col2:
            annual_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, value=5.0, step=0.1)
        with col3:
            years = st.number_input("Loan Term (Years)", min_value=1, value=30, step=1)
        
        if st.button("Calculate Amortization", type="primary"):
            monthly_payment, total_interest, total_payment, schedule = calculate_amortization(
                principal, annual_rate, years
            )
            
            st.write("### Results")
            col1, col2, col3 = st.columns(3)
            col1.metric("Monthly Payment", f"${monthly_payment:,.2f}")
            col2.metric("Total Interest", f"${total_interest:,.2f}")
            col3.metric("Total Payment", f"${total_payment:,.2f}")
            
            st.write("### Amortization Schedule")
            st.dataframe(schedule, use_container_width=True)
            
            st.write("### Payment Breakdown Chart")
            chart_data = schedule[['Month', 'Principal', 'Interest']].set_index('Month')
            st.bar_chart(chart_data)

if __name__ == "__main__":
    main()
