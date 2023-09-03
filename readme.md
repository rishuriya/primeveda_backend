# Primeveda Django Server

Primeveda is a Django server application that specializes in generating stories based on the essence of Indian ancient texts. This application leverages the Palm API to generate stories and content. In the future, we plan to transition to our own NLP (Natural Language Processing) model once we collect enough data and release our main app.

## Features

- Story Generation: Generate stories with Indian cultural and ancient text influences.
- Integration with Palm API: Utilize the Palm API for text generation.
- Future NLP Model: Planning to develop and integrate our own NLP model for improved story generation.

## Installation

1. **Clone this repository to your local machine:**

   ```bash
   git clone https://github.com/rishuriya/primeveda-django.git
2. **Navigate to the project directory:**
    ```bash
    cd primeveda-django
3. **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
4. **Install the Project depedencies:**
    ```bash
    pip install -r requirements.txt

5. **Download Spacy nlp for similarity algorithms**
    ```
    python -m spacy download en_core_web_md
    ```
6. **Create an `.env` file in the project directory with the following content:**

   ```
    SECRET_KEY=Add your value
    DEBUG=True
    EMAIL_HOST=smtp.gmail.com
    EMAIL_PORT=587
    EMAIL_HOST_USER = email
    EMAIL_HOST_PASSWORD = app password
    PALM_API_KEY = Palm api key
   ```

   Replace the placeholders with your actual values.

7. **Run database migrations:**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

8. **Run the Django development server:**

   ```bash
   python manage.py runserver
   ```

9. **Access the server at `http://127.0.0.1:8000/`.**


## API Endpoints

- **Register User**
  - URL: `api/register/`
  - Description: Register a new user account.
  - Method: POST

- **Activate User Account**
  - URL: `api/activate/<str:uidb64>/<str:token>/`
  - Description: Activate a user account using a unique token.
  - Method: GET

- **Sign In**
  - URL: `api/sign-in/`
  - Description: Sign in to an existing user account.
  - Method: POST

- **Generate Story**
  - URL: `api/generate-story/`
  - Description: Generate a story based on Indian ancient text.
  - Method: POST

- **Current User Detail**
  - URL: `api/current-user/`
  - Description: Retrieve details of the currently logged-in user.
  - Method: GET

- **Search API**
  - URL: `api/search/`
  - Description: Search for stories based on user queries. if not available it will generate the story.
  - Method: POST

- **Update Profile**
  - URL: `api/update-profile/`
  - Description: Edit the profile of the current user.
  - Method: PUT


