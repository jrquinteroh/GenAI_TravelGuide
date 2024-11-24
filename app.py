import streamlit as st
import os
import pathlib
import textwrap
from PIL import Image

import google.generativeai as genai

# Configure the GenAI API key
genai.configure(api_key='AIzaSyBU10JXBIC5tQ5dfG2od0L3ueVu1MQgIpk')  # Replace with your actual API key

# Set page config
st.set_page_config(page_title="Personalized Trip Plan Recommendations", layout="wide")

# Custom CSS for better-looking boxes
st.markdown("""
<style>
    .stCheckbox {
        padding: 10px;
    }
    .recommendation-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Function to get the response from the GenAI
def get_gemini_response(prompt):
    model = genai.GenerativeModel('gemini-pro')  # Use the appropriate model name
    response = model.generate_content(prompt)
    return response.text

# Function to fetch recommendations
def fetch_recommendations(destination, duration, num_travellers, interests, budget_per_person):
    # Create the prompt using user inputs
    total_budget = budget_per_person * num_travellers * duration
    prompt = (
        f"Generate personalized daily plan recommendations for a trip to {destination} "
        f"for {duration} days with {int(num_travellers)} traveller(s). "
        f"The travellers are interested in {interests}. "
        f"The total budget for the trip is ${total_budget:.2f}, "
        f"which is approximately ${budget_per_person:.2f} per person per day. "
        f"Please ensure that the recommended activities and restaurants fit within this budget. "
        f"For each day, provide recommendations for morning, midday, afternoon/evening activities, "
        f"and recommended restaurants, including estimated costs. "
        f"Please format the response as follows:\n\n"
        f"Day X:\n"
        f"Morning Plan:\n"
        f"Description: [Brief description]\n"
        f"Estimated Cost: $X\n"
        f"Activities:\n"
        f"- Activity 1\n"
        f"- Activity 2\n"
        f"Midday Plan:\n"
        f"Description: [Brief description]\n"
        f"Estimated Cost: $X\n"
        f"Activities:\n"
        f"- Activity 1\n"
        f"- Activity 2\n"
        f"Afternoon/Evening Plan:\n"
        f"Description: [Brief description]\n"
        f"Estimated Cost: $X\n"
        f"Activities:\n"
        f"- Activity 1\n"
        f"- Activity 2\n"
        f"Recommended Restaurants:\n"
        f"- Restaurant 1\n"
        f"- Restaurant 2\n"
        f"\nPlease ensure each day's plan follows this exact format."
    )

    # Get the generated text from the GenAI
    generated_text = get_gemini_response(prompt)

    # Display the generated text for debugging
    st.write("**Generated Text:**")
    st.write(generated_text)

    # Parse the generated text to extract plan details
    recommendations = {}
    lines = generated_text.strip().split('\n')
    current_day = ''
    current_section = ''
    current_plan = {}
    in_activities_section = False

    for line in lines:
        line = line.strip()
        if line.startswith("Day"):
            if current_day and current_plan:
                recommendations[current_day] = current_plan
            current_day = line
            current_plan = {}
            current_section = ''
            in_activities_section = False
        elif line.endswith("Plan:"):
            current_section = line
            current_plan[current_section] = {"description": "", "estimated_cost": "", "activities": []}
            in_activities_section = False
        elif line.startswith("Description:"):
            if current_section in current_plan:
                current_plan[current_section]["description"] = line.replace("Description:", "").strip()
        elif line.startswith("Estimated Cost:"):
            if current_section in current_plan:
                current_plan[current_section]["estimated_cost"] = line.replace("Estimated Cost:", "").strip()
        elif line == "Activities:":
            in_activities_section = True
        elif in_activities_section and line.startswith(("-", "*", "•")):
            activity = line.lstrip("-*• ").strip()
            if current_section in current_plan:
                current_plan[current_section]["activities"].append(activity)
        elif line == "Recommended Restaurants:":
            current_plan["Recommended Restaurants"] = []
            in_activities_section = False
            current_section = "Recommended Restaurants"
        elif current_section == "Recommended Restaurants" and line.startswith(("-", "*", "•")):
            restaurant = line.lstrip("-*• ").strip()
            current_plan["Recommended Restaurants"].append(restaurant)
        elif not line:
            in_activities_section = False

    # Add the last day's plan
    if current_day and current_plan:
        recommendations[current_day] = current_plan

    return recommendations

# Collect user inputs
st.title("Personalized Trip Plan Recommendations")

destination = st.text_input("City of Destination")
duration = st.number_input("Duration of Trip (in days)", min_value=1, step=1)
num_travellers = st.number_input("Number of Travellers", min_value=1, step=1)
interests = st.text_input("Hobbies/Interests (separate by commas)")
budget_per_person = st.number_input("Budget per Person per Day ($)", min_value=0.0, step=10.0)

if st.button("Generate Recommendations"):
    if destination and duration and num_travellers and interests and budget_per_person:
        # Fetch recommendations
        recommendations = fetch_recommendations(destination, duration, num_travellers, interests, budget_per_person)

        # Display recommendations
        st.write("Select the plans you'd like to follow:")

        # Store selected plans in session state
        if 'selected_plans' not in st.session_state:
            st.session_state.selected_plans = set()

        if recommendations:
            # Iterate over the fetched recommendations
            for day, plans in recommendations.items():
                st.subheader(day)
                for plan_section, details in plans.items():
                    if plan_section == "Recommended Restaurants":
                        st.write("**Recommended Restaurants:**")
                        for restaurant in details:
                            st.write(f"- {restaurant}")
                        continue

                    col1, col2 = st.columns([1, 4])

                    with st.container():
                        st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)

                        # Checkbox in the first column
                        with col1:
                            plan_key = f"{day} - {plan_section}"
                            if st.checkbox("Select", key=plan_key):
                                st.session_state.selected_plans.add(plan_key)
                            else:
                                st.session_state.selected_plans.discard(plan_key)

                        # Plan details in the second column
                        with col2:
                            st.write(f"**{plan_section}**")
                            st.write(f"**Description:** {details['description']}")
                            st.write(f"**Estimated Cost:** {details['estimated_cost']}")
                            with st.expander("View Activities"):
                                for activity in details["activities"]:
                                    st.write(f"• {activity}")

                        st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("No recommendations available.")
    else:
        st.warning("Please fill in all the fields.")

# Show selected plans
if 'selected_plans' in st.session_state and st.session_state.selected_plans:
    st.sidebar.header("Selected Plans")
    for plan in st.session_state.selected_plans:
        st.sidebar.write(f"✓ {plan}")

    if st.sidebar.button("Start Selected Plans"):
        st.sidebar.success("Plans activated! You can now begin following your selected plans.")
else:
    st.sidebar.info("Select at least one plan to get started")
