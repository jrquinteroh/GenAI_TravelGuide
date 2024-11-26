import streamlit as st
import os
from PIL import Image
import google.generativeai as genai
from datetime import datetime, timedelta
from fpdf import FPDF
import base64

# Set page config (Must be the first Streamlit command)
st.set_page_config(page_title="Personalized Trip Planner", layout="wide")

# Custom CSS for styling and alignment
st.markdown("""
<style>
    /* Center align the main title */
    .center-title .block-container h1 {
        text-align: center;
    }
    /* Center align the tabs */
    div[class*="stTabs"] > div {
        justify-content: center;
    }
    /* Center align content in the Checkout tab */
    .checkout-content {
        text-align: center;
    }
    /* Additional styling */
    .recommendation-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
        display: flex;
        align-items: center;
    }
    .recommendation-image {
        width: 300px;
        height: 200px;
        object-fit: cover;
        border-radius: 5px;
        margin-right: 10px;
    }
    .plan-details {
        flex-grow: 1;
    }
    .select-checkbox {
        margin-left: auto;
        margin-right: 10px;
    }
    .counter {
        display: flex;
        align-items: center;
    }
    .counter button {
        padding: 5px 10px;
        font-size: 16px;
    }
    .counter span {
        margin: 0 10px;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Center the main title
with st.container():
    st.markdown('<div class="center-title">', unsafe_allow_html=True)
    st.title("Personalized Trip Planner")
    st.markdown('</div>', unsafe_allow_html=True)

# Tabs for page navigation in the specified order, centered
tab_names = ["Chatbot", "Input", "Recommendations", "Checkout"]
tabs = st.tabs(tab_names)

tab_chatbot, tab_input, tab_recommendations, tab_checkout = tabs



# Define the function to get a response from Gemini
def get_gemini_response(question, chat_history):
    """
    Calls the Gemini model (gemini-pro) and returns a response to the given question,
    including the chat history for context.
    """

    # Configure the API key
    API_KEY = st.secrets["API_KEY"]  # Replace with your valid API key
    genai.configure(api_key=API_KEY)
    
    # Instantiate the model
    model = genai.GenerativeModel('gemini-pro')

    # Combine the chat history with the current question
    conversation = "\n".join(chat_history + [f"User: {question}"])

    # Call the method with the conversation
    response = model.generate_content(conversation)

    # Update the chat history
    chat_history.extend([f"User: {question}", f"Assistant: {response.text}"])

    # Return the response and updated chat history
    return response.text, chat_history

with tab_chatbot:
    st.header("Chatbot Assistant")

    # Add the image at the beginning
    st.image("Travel_chatbot.png", use_container_width=True)  # Ensure the file is in the same directory

    # Add the descriptive text below the image
    st.markdown("""
    ### Not sure where to go?  
    Let our chatbot inspire you with personalized travel ideas based on your preferences.  
    Start your journey with just a conversation!
    """)

    # Add a "Refresh" button with a unique key
    if st.button("Refresh", key="refresh_chatbot"):
        st.session_state.chat_messages = []  # Clear the chat history
        st.session_state.chat_history = []  # Clear the conversation history
        st.experimental_rerun()  # Refresh the app to reset the state

    # Initialize chat message history in session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display past messages
    for message in st.session_state.chat_messages:
        if 'role' in message and 'content' in message:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input field for the user to ask questions
    prompt = st.chat_input("Ask me anything about travel:")
    if prompt:
        # Add user input to the message history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get the response from the assistant
        try:
            answer, st.session_state.chat_history = get_gemini_response(prompt, st.session_state.chat_history)
            st.session_state.chat_messages.append({"role": "assistant", "content": answer})

            # Display the assistant's response
            with st.chat_message("assistant"):
                st.markdown(answer)

        except Exception as e:
            st.error(f"An error occurred: {e}")

def fetch_recommendations():
    # Create recommendations using images from '1.jpeg' to '7.jpeg'
    recommendations = {}
    image_files = [f"{i}.jpeg" for i in range(1, 8)]  # '1.jpeg' to '7.jpeg'
    for i, image_file in enumerate(image_files, start=1):
        day = f"Day {i}"
        recommendations[day] = {
            "description": f"Description for Plan {i}",
            "estimated_cost": f"${20 * i}",  # Example cost
            "image_file": image_file  # Use specified images
        }
    return recommendations

def display_recommendation_card(day, details):
    plan_key = day  # Using day as the key
    # Initialize selected_plans as a dictionary
    if 'selected_plans' not in st.session_state:
        st.session_state['selected_plans'] = {}

    # Create two columns: one for the image, one for the selection and counter
    col_image, col_controls = st.columns([3, 1])

    with col_image:
        # Display the image
        image_file = details.get('image_file')
        if os.path.exists(image_file):
            image = Image.open(image_file)
            st.image(image, use_container_width=True)
        else:
            st.error(f"Image {image_file} not found.")

    with col_controls:
        # Checkbox to select the plan
        selected = st.checkbox("Select", key=f"{plan_key}_select")

        # Number of people adjustment
        if selected:
            num_people = st.number_input("Number of People", min_value=1, step=1, key=f"{plan_key}_num_people")
            # Store the selected plan with the number of people and image file
            st.session_state['selected_plans'][plan_key] = {
                'description': details['description'],
                'estimated_cost': details['estimated_cost'],
                'num_people': num_people,
                'image_file': details['image_file']
            }
        else:
            # Remove the plan from selected_plans if unchecked
            if plan_key in st.session_state['selected_plans']:
                del st.session_state['selected_plans'][plan_key]

def recommendations_page():
    st.header("Recommendations")

    if 'destination' not in st.session_state:
        st.warning("Please complete the Input tab before proceeding to Recommendations.")
    else:
        # Fetch recommendations if not already fetched
        if 'recommendations' not in st.session_state:
            st.session_state['recommendations'] = fetch_recommendations()

        recommendations = st.session_state['recommendations']

        # Display image placeholders with selection options
        st.subheader("Select Your Preferred Plan for a Day")

        for day, details in recommendations.items():
            # Only display the day and its plan
            display_recommendation_card(day, details)

# Import FPDF for PDF generation
from fpdf import FPDF
import base64

def checkout_page():
    st.header("Checkout")

    # Center align all content
    st.markdown("<div class='checkout-content'>", unsafe_allow_html=True)

    # Display general trip information from "Trip Details Input" tab
    city = st.session_state.get('destination', 'your destination')
    st.subheader(f"Your Trip Details for {city}")

    # Collect trip details
    start_date = st.session_state.get('start_date', datetime.today())
    duration = st.session_state.get('duration', 1)
    end_date = start_date + timedelta(days=duration - 1)
    trip_details = {
        "Trip Dates": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "Duration": f"{duration} days",
        "Accommodation Location": st.session_state.get('accommodation_location', 'Not specified'),
        "Number of Travellers": int(st.session_state.get('num_travellers', 1)),
        "Number of Children": int(st.session_state.get('num_children', 0)),
        "Pets Allowed": 'Yes' if st.session_state.get('pets_allowed', False) else 'No',
        "Wheelchair Accessible Required": 'Yes' if st.session_state.get('wheelchair_accessible', False) else 'No',
        "Preferred Transportation": ', '.join(st.session_state.get('transportation', [])) if st.session_state.get('transportation') else 'N/A',
        "Interests": st.session_state.get('interests', 'N/A'),
        "Plan Type Preference": st.session_state.get('plan_type', 'N/A')
    }

    # Display trip details
    for key, value in trip_details.items():
        st.write(f"- **{key}:** {value}")

    st.write("---")

    # Display the selected plan(s)
    if 'selected_plans' in st.session_state and len(st.session_state['selected_plans']) > 0:
        st.subheader("Your Selected Plan(s) For Your Specified Day(s):")
        total_estimated_cost = 0

        # Counter for activities
        activity_counter = 1

        # Prepare plan details for PDF
        plan_details_list = []

        for plan_key, plan_info in st.session_state['selected_plans'].items():
            st.write(f"**Activity #{activity_counter}**")
            st.write(f"- Description: {plan_info['description']}")
            st.write(f"- Estimated Cost: {plan_info['estimated_cost']}")
            st.write(f"- Number of People: {plan_info['num_people']}")

            # Display the image associated with the plan
            image_file = plan_info.get('image_file')
            if image_file:
                try:
                    st.image(image_file, width=300)
                except Exception as e:
                    st.error(f"Error loading image {image_file}: {e}")
                    st.write("Image not available.")
            else:
                st.write("No image available for this plan.")

            # Extract numerical cost for total calculation
            cost_str = plan_info['estimated_cost'].replace('$', '').strip()
            try:
                cost = float(cost_str)
                total_estimated_cost += cost * plan_info['num_people']
            except ValueError:
                total_estimated_cost += 0  # Handle cases where cost is not a number

            # Add plan info to the list for PDF
            plan_details_list.append({
                "Activity": f"Activity #{activity_counter}",
                "Description": plan_info['description'],
                "Estimated Cost": plan_info['estimated_cost'],
                "Number of People": plan_info['num_people'],
                "Image File": image_file
            })

            activity_counter += 1  # Increment the activity counter

        st.write(f"**Total Estimated Cost For Your Activities For Your Selected Day:** ${total_estimated_cost:.2f}")

        # Generate PDF report using FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)

        # Title
        pdf.cell(0, 10, f"Trip Report for {city}", ln=True, align='C')

        # Trip Details
        pdf.set_font("Arial", '', 12)
        pdf.ln(10)
        pdf.cell(0, 10, "Trip Details:", ln=True)
        for key, value in trip_details.items():
            pdf.cell(0, 10, f"{key}: {value}", ln=True)

        # Selected Plans
        pdf.ln(10)
        pdf.cell(0, 10, "Selected Plans:", ln=True)
        for plan in plan_details_list:
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, plan["Activity"], ln=True)
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, f"Description: {plan['Description']}", ln=True)
            pdf.cell(0, 10, f"Estimated Cost: {plan['Estimated Cost']}", ln=True)
            pdf.cell(0, 10, f"Number of People: {plan['Number of People']}", ln=True)
            # Include image if available
            if plan["Image File"]:
                try:
                    pdf.image(plan["Image File"], w=100)
                except Exception as e:
                    pass  # Handle cases where the image cannot be loaded

        # Total Estimated Cost
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Total Estimated Cost: ${total_estimated_cost:.2f}", ln=True)

        # Get PDF content as bytes
        pdf_bytes = pdf.output(dest='S').encode('latin1')

        # Provide the PDF for download
        st.download_button(
            label="Download Report",
            data=pdf_bytes,
            file_name="Trip_Report.pdf",
            mime="application/pdf",
            key="download_report"
        )


        if st.button("Confirm and Finish", key="confirm_finish"):
            st.success("Your trip has been planned! Thank you for using TravelPal 😎")
            st.balloons()  # Display balloons when the trip is confirmed
    else:
        st.warning("You have not selected any plans.")
        st.write("Please go back to the Recommendations tab to select plans.")

    st.markdown("</div>", unsafe_allow_html=True)  # Close center alignment


with tab_input:
    st.header("Trip Details Input")

    destination = st.text_input("City of Destination")
    duration = st.number_input("Duration of Trip (in days)", min_value=1, step=1)
    start_date = st.date_input("Date of Travel", min_value=datetime.today())
    accommodation_location = st.text_input("Accommodation Location (optional)")
    num_travellers = st.number_input("Number of Travellers", min_value=1, step=1)
    num_children = st.number_input("Number of Children among the Travellers", min_value=0, step=1)
    pets_allowed = st.checkbox("Include Pet-friendly Options")
    wheelchair_accessible = st.checkbox("Require Wheelchair Accessible Options")

    transportation_options = ['Car', 'Public Transport', 'Boat', 'Bicycle', 'Walking']
    transportation = st.multiselect("Preferred Modes of Transportation", transportation_options)

    if 'Car' in transportation:
        st.markdown("[🚗 Click here to rent a car!](https://www.example.com/car-rental)")  # Replace with actual link

    if 'Public Transport' in transportation:
        st.markdown("[🚍 Click here to view public transport details!](https://www.example.com/car-rental)")

    if 'Boat' in transportation:
        st.markdown("[🛥️ Click here to view transport via boat (fancy😎💰)!](https://www.example.com/car-rental)")

    if 'Bicycle' in transportation:
        st.markdown("[🚲 Click here to view bicycle routes!](https://www.example.com/car-rental)")

    if 'Walking' in transportation:
        st.markdown("[🚶‍♂️‍➡️🚶‍♀️ Click here to walking routes!](https://www.example.com/car-rental)")
    
    interests = st.text_input("Hobbies/Interests (separate by commas)")
    budget_per_person = st.number_input("Budget per Person per Day ($)", min_value=0.0, step=10.0)
    plan_type = st.selectbox("Preferred Plan Type", ["Very Touristy Plans", "Local Plans", "Not-Touristy Plans At All"])
    randomize_interests = st.checkbox("Randomize Interests (Get alternative recommendations)")

    # --- Added Section Starts Here ---
    # Display plans generated by GenAI based on user inputs
    if st.button("Generate Plans"):
        # Prepare the prompt using user inputs
        prompt = f"""
        Based on the following trip details, generate a personalized travel plan:
        - Destination: {destination}
        - Duration: {duration} days
        - Start Date: {start_date.strftime('%Y-%m-%d')}
        - Accommodation Location: {accommodation_location if accommodation_location else 'Not specified'}
        - Number of Travellers: {int(num_travellers)}
        - Number of Children: {int(num_children)}
        - Pets Allowed: {'Yes' if pets_allowed else 'No'}
        - Wheelchair Accessible Required: {'Yes' if wheelchair_accessible else 'No'}
        - Preferred Transportation: {', '.join(transportation) if transportation else 'N/A'}
        - Interests: {interests}
        - Budget per Person per Day: ${budget_per_person}
        - Plan Type Preference: {plan_type}
        - Randomize Interests: {'Yes' if randomize_interests else 'No'}
        """

        # Initialize chat history if not already present
        if 'chat_history' not in st.session_state:
            st.session_state['chat_history'] = []

        # Get the response from the GenAI model
        try:
            plans_text, st.session_state['chat_history'] = get_gemini_response(
                prompt, st.session_state['chat_history']
            )
            st.subheader("Generated Plans:")
            st.write(plans_text)
        except Exception as e:
            st.error(f"An error occurred while generating plans: {e}")

    # --- Added Section Ends Here ---

    if st.button("Proceed", key="proceed_input"):
        if destination and duration and num_travellers and interests and budget_per_person:
            # Save inputs to session state
            st.session_state['destination'] = destination
            st.session_state['duration'] = duration
            st.session_state['start_date'] = start_date
            st.session_state['accommodation_location'] = accommodation_location
            st.session_state['num_travellers'] = num_travellers
            st.session_state['num_children'] = num_children
            st.session_state['has_children'] = num_children > 0
            st.session_state['pets_allowed'] = pets_allowed
            st.session_state['wheelchair_accessible'] = wheelchair_accessible
            st.session_state['transportation'] = transportation
            st.session_state['interests'] = interests
            st.session_state['budget_per_person'] = budget_per_person
            st.session_state['plan_type'] = plan_type
            st.session_state['randomize_interests'] = randomize_interests

            st.success("Inputs saved. Please proceed to the Recommendations tab.")
        else:
            st.warning("Please fill in all the required fields.")

with tab_recommendations:
    recommendations_page()

with tab_checkout:
    checkout_page()
