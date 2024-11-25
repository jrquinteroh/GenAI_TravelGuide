import streamlit as st
import os
import pathlib
import textwrap
from PIL import Image
import google.generativeai as genai
from datetime import datetime

# Configure the GenAI API key
genai.configure(api_key='AIzaSyBU10JXBIC5tQ5dfG2od0L3ueVu1MQgIpk')  # Replace with your actual API key

# Set page config
st.set_page_config(page_title="Personalized Trip Plan Recommendations", layout="wide")

# Custom CSS for better-looking cards - updated to match the travel card design
st.markdown("""
<style>
    .recommendation-card {
        background-color: #1e4d6b;
        color: white;
        border-radius: 20px;
        padding: 20px;
        margin: 20px 0;
        position: relative;
        overflow: hidden;
    }
    .info-panel {
        background-color: rgba(30, 77, 107, 0.8);
        padding: 10px;
        border-radius: 10px;
        margin-top: 10px;
    }
    .rating {
        color: #FFD700;
        font-size: 24px;
    }
    .price-tag {
        background-color: rgba(30, 77, 107, 0.9);
        padding: 10px 20px;
        border-radius: 15px;
        position: absolute;
        right: 20px;
        bottom: 20px;
    }
    .nav-arrow {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        font-size: 24px;
        color: white;
        cursor: pointer;
    }
    .nav-arrow.left {
        left: 10px;
    }
    .nav-arrow.right {
        right: 10px;
    }
    .stCheckbox {
        padding: 10px;
    }
    .activity-icon {
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Function to get the response from the GenAI
def get_gemini_response(prompt):
    model = genai.GenerativeModel('gemini-pro')  # Use the appropriate model name
    response = model.generate_content(prompt)
    return response.text

# Function to fetch recommendations
def fetch_recommendations(destination, duration, num_travellers, interests, budget_per_person, start_date, accommodation_location, has_children, plan_type, randomize):
    # Create the prompt using user inputs
    total_budget = budget_per_person * num_travellers * duration
    date_str = start_date.strftime("%B %Y")  # Format the date as 'Month Year'
    children_text = "including children" if has_children else "without children"
    accommodation_text = f"They are staying near {accommodation_location}. " if accommodation_location else ""
    randomize_text = "Please provide alternative recommendations that differ from their stated hobbies/interests. " if randomize else ""
    plan_type_text = f"Focus on providing {plan_type.lower()}."

    prompt = (
        f"Generate personalized daily plan recommendations for a trip to {destination} "
        f"starting on {date_str} for {duration} days with {int(num_travellers)} traveller(s) {children_text}. "
        f"The travellers are interested in {interests}. "
        f"{accommodation_text}"
        f"The total budget for the trip is ${total_budget:.2f}, "
        f"which is approximately ${budget_per_person:.2f} per person per day. "
        f"Please ensure that the recommended activities and restaurants fit within this budget. "
        f"{plan_type_text} "
        f"{randomize_text}"
        f"For each day, provide recommendations for morning, midday, afternoon/evening activities, "
        f"and recommended restaurants, including estimated costs. "
        f"Please consider the season and weather for {date_str}. "
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

# Function to display recommendation cards
def display_recommendation_card(day, plan_section, details, image_url=None):
    with st.container():
        st.markdown(f'''
        <div class="recommendation-card">
            <div class="nav-arrow left">←</div>
            <div class="nav-arrow right">→</div>
            <h3>{day} - {plan_section}</h3>
            <p>{details['description']}</p>
            <div class="info-panel">
                <span class="activity-icon">⏱</span> Duration: {details.get('duration', '2-3 hours')}
                <br/>
                <span class="activity-icon">👥</span> {'Child-friendly' if has_children else 'Adult-focused'}
                <br/>
                <span class="activity-icon">♿</span> Wheelchair accessible
            </div>
            <div class="rating">★★★★★</div>
            <div class="price-tag">
                {details['estimated_cost']}
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Checkbox for selection
        plan_key = f"{day} - {plan_section}"
        if st.checkbox("Select this plan", key=plan_key):
            st.session_state.selected_plans.add(plan_key)
        else:
            st.session_state.selected_plans.discard(plan_key)
        
        # Expandable activities section
        with st.expander("View Activities"):
            for activity in details["activities"]:
                st.write(f"• {activity}")

# Collect user inputs
st.title("Personalized Trip Plan Recommendations")

destination = st.text_input("City of Destination")
duration = st.number_input("Duration of Trip (in days)", min_value=1, step=1)
start_date = st.date_input("Date of Travel")
accommodation_location = st.text_input("Accommodation Location (optional)")
num_travellers = st.number_input("Number of Travellers", min_value=1, step=1)
has_children = st.checkbox("Are there children among the travellers?")
interests = st.text_input("Hobbies/Interests (separate by commas)")
budget_per_person = st.number_input("Budget per Person per Day ($)", min_value=0.0, step=10.0)
plan_type = st.selectbox("Preferred Plan Type", ["Very Touristy Plans", "Local Plans", "Not-Touristy Plans At All"])
randomize_interests = st.checkbox("Randomize Interests (Get alternative recommendations)")

if st.button("Generate Recommendations"):
    if destination and duration and num_travellers and interests and budget_per_person:
        # Handle randomize interests
        randomize = randomize_interests

        # Fetch recommendations
        recommendations = fetch_recommendations(
            destination, duration, num_travellers, interests, budget_per_person,
            start_date, accommodation_location, has_children, plan_type, randomize
        )

        st.write("### Your Personalized Travel Plans")
        st.write("Select the plans you'd like to include in your itinerary:")

        # Store selected plans in session state
        if 'selected_plans' not in st.session_state:
            st.session_state.selected_plans = set()

        if recommendations:
            for day, plans in recommendations.items():
                st.subheader(day)
                for plan_section, details in plans.items():
                    if plan_section != "Recommended Restaurants":
                        display_recommendation_card(day, plan_section, details)
                # Display restaurants separately
                if "Recommended Restaurants" in plans:
                    with st.expander("🍽️ Recommended Restaurants"):
                        for restaurant in plans["Recommended Restaurants"]:
                            st.write(f"• {restaurant}")
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
