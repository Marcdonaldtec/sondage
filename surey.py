import pickle
import os
import csv
import boto3
import io


# AWS S3 configuration
AWS_ACCESS_KEY_ID = 'AKIATPRQOVAG52WSPTEC'
AWS_SECRET_ACCESS_KEY = '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'
BUCKET_NAME = 'esihondagebucket'

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def create_survey():
    survey_data = {
        "Intentions de quitter le pays": {
            "Avez-vous l'intention de quitter le pays après avoir terminé vos études universitaires?": ["Oui", "Non", "Incertain"]
        },
        "Tranche d'âge": {
            "Quel est votre âge actuel?": ["Moins de 20 ans", "20-24 ans", "25-29 ans", "30-34 ans", "35 ans et plus"]
        },
        "Niveau d'études": {
            "À quel niveau d'études êtes-vous actuellement?": ["Licence 1", "Licence 2", "Licence 3", "Licence 4", "DUT 1", "DUT 2"]
        },
        "Pays visé": {
            "Vers quel(s) pays envisagez-vous de vous rendre?": ["États-Unis", "Canada", "Royaume-Uni", "Australie", "France", "Autre"]
        },
        "Raison du départ": {
            "Pourquoi envisagez-vous de quitter le pays?": ["Opportunités professionnelles", "Recherche académique", "Qualité de vie", "Autre"]
        },
        "Objectif du départ": {
            "Envisagez-vous de quitter le pays pour des études supplémentaires ou d'autres raisons?": ["Études supplémentaires", "Raisons professionnelles", "Raisons personnelles"]
        },
        "Durée prévue à l'étranger": {
            "Si vous envisagez un départ temporaire, quelle est la durée prévue de votre séjour?": ["Moins d'un an", "1-2 ans", "3-5 ans", "Plus de 5 ans"]
        },
        "Intention de retour dans le pays d'origine": {
            "Avez-vous l'intention de retourner dans votre pays d'origine après votre séjour à l'étranger?": ["Oui", "Non", "Incertain"]
        }
    }

    return survey_data

def load_existing_responses(file_name):
    existing_responses = []
    if os.path.exists(file_name):
        with open(file_name, "rb") as existing_file:
            try:
                while True:
                    response = pickle.load(existing_file)
                    existing_responses.append(response)
            except EOFError:
                pass
    return existing_responses

def save_survey_response(data, file_name):
    with open(file_name, "ab") as pickle_file:
        pickle.dump(data, pickle_file)

    # Save response to AWS S3 as a CSV file
    csv_data = [[question, answer] for question, answer in data.items()]
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)

    # Check if the existing CSV file exists in S3
    existing_responses_key = 'responses/all_responses1.csv'
    try:
        existing_csv_object = s3.get_object(Bucket=BUCKET_NAME, Key=existing_responses_key)
        existing_csv_content = existing_csv_object['Body'].read().decode('utf-8')
        csv_buffer.write(existing_csv_content)
    except s3.exceptions.NoSuchKey:
        # If the file doesn't exist yet, write header
        csv_writer.writerow(["Response"] + list(data.keys()))

    # Append the new response to the CSV file
    csv_writer.writerow([len(existing_responses) + 1] + [f"{i + 1}. {answer}" for i, answer in enumerate(data.values())])

    # Convert the string buffer to bytes
    csv_bytes = csv_buffer.getvalue().encode('utf-8')

    # Upload the updated CSV file to S3
    s3.put_object(Body=csv_bytes, Bucket=BUCKET_NAME, Key=existing_responses_key)

def display_survey_responses(responses):
    if responses:
        print("Survey Responses:")
        for index, response in enumerate(responses, start=1):
            print(f"Response {index}:")
            for question, answer in response.items():
                print(f"{question}: {answer}")
            print()
    else:
        print("No existing survey responses.")

if __name__ == "__main__":
    file_name = "survey_responses.pkl"
    existing_responses = load_existing_responses(file_name)

    while True:
        print("\n1. Add new responses")
        print("2. Show existing details")
        print("3. Exit")
        choice = input("Enter your choice (1, 2, or 3): ")

        if choice == "1":
            survey = create_survey()

            user_responses = {}
            for section, questions in survey.items():
                print(f"\n{section}:")
                for question, options in questions.items():
                    print(f"{question}")
                    for i, option in enumerate(options, start=1):
                        print(f"{i}. {option}")
                    user_input = input("Your choice (1, 2, 3, ...): ")
                    selected_option = options[int(user_input) - 1] if 1 <= int(user_input) <= len(options) else "Invalid choice"
                    user_responses[question] = selected_option

            # Save each response individually
            save_survey_response(user_responses, file_name)
            print("New survey response added and saved successfully.")
        elif choice == "2":
            display_survey_responses(existing_responses)
        elif choice == "3":
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter either '1', '2', or '3'.")
