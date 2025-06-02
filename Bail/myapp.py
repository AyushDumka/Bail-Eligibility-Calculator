from flask import Flask, render_template, request, jsonify  # Import jsonify
from datetime import datetime, timedelta
import pandas as pd


app = Flask(__name__)
sections_data = pd.read_excel("/home/baileligibilitycalculator/UTRC/sections_data_gujarat.xlsx")
ndps_data = pd.read_excel("/home/baileligibilitycalculator/UTRC/ndps.xlsx")
ipc_data = pd.read_excel("/home/baileligibilitycalculator/UTRC/IPC.xlsx")
pocso_data = pd.read_excel("/home/baileligibilitycalculator/UTRC/POCSO.xlsx")
test_col = pd.read_excel("/home/baileligibilitycalculator/UTRC/ndps.xlsx", usecols=['Sections'])

@app.route('/')
def index():
    return render_template("initial.html")


@app.route('/newfile.html')
def newfile():
    column_values = test_col['Sections'].tolist()
    return render_template("newfile.html", column_values=column_values)


@app.route('/input1')
def input1():
    return render_template("test_input1.html")

@app.route('/input2')
def input2():
    return render_template("test_input2.html")


@app.route('/check_eligibility', methods=['POST'])
def check_bail_eligibility():
    if request.method == "POST":


        act = request.form.get("act")
        name = request.form.get("name")
        section = request.form.get("section")
        section = str(section)
        gender = request.form.get("gender")
        age = int(request.form.get("age"))
        sentence_status = request.form.get("sentence_status","no").lower()
        #default value added to avoid exception in form2
        max_punishment = float(request.form.get("max_punishment"))
        date_sent_to_jail = request.form.get("date_sent_to_jail")
        compoundable = request.form.get("compoundable").lower() == "yes"
        bailable = request.form.get("bailable").lower() == "yes"
        bail_date = None
        bail_received = request.form.get("bail_received","no").lower() == "yes"
        surety_furnished = request.form.get("surety_furnished","no").lower() == "yes"
        if "Gujarat Prohibition Act" in act:
            probation_act = "no"
        else:
            probation_act = request.form.get("probation_act","no").lower() == "yes"
        chargesheet_filed = request.form.get("chargesheet_filed").lower() == "yes"
        detained_under_crpc = request.form.get("detained_under_crpc","no").lower() == "yes"
        sick_or_infirm = request.form.get("sick_or_infirm","no").lower() == "yes"
        first_time_offender = request.form.get("first_time_offender","no").lower() == "yes"
        unsound_mind = request.form.get("unsound_mind","no").lower() == "yes"
        magistrate_trial = request.form.get("magistrate_trial").lower() == "yes"
        first_date_fixed_for_evidence = request.form.get("first_date_fixed_for_evidence")
        trial_concluded = request.form.get("trial_concluded","no").lower() == "yes"


        date_sent_to_jail = datetime.strptime(date_sent_to_jail, "%Y-%m-%d")

        current_date = datetime.now()

        days_in_jail = (current_date - date_sent_to_jail).days

        max_punishment = max_punishment * 365

        jail_duration_percentage = (days_in_jail / max_punishment) * 100


        if gender == "Female":
            is_woman = "yes"
        else:
            is_woman = "no"

        if age >=19 and age <=21:
            age_between_19_and_21 = "yes"
        else:
            age_between_19_and_21 = "no"

        # Initialize a list to keep track of eligibility conditions met
        eligibility_conditions = []


        # Condition 1
        if days_in_jail >= max_punishment / 2:
            eligibility_conditions.append("2.2.1")

         # Condition 2
        if bail_received:
            if not surety_furnished:
                eligibility_conditions.append("2.2.2")


        # Condition 3
        if compoundable:
            eligibility_conditions.append("2.2.3")

        # Condition 4
        if bailable:
            eligibility_conditions.append("2.2.4")


        # Condition 5
        if probation_act == "yes":
            eligibility_conditions.append("2.2.5")


        #Condition 6
        if sentence_status == "yes":
            eligibility_conditions.append("2.2.6")


        # Condition 7
        if not chargesheet_filed:
            if max_punishment < 10 * 365 and days_in_jail > 60:
                eligibility_conditions.append("2.2.7")
                bail_date = date_sent_to_jail + timedelta(days=60)
            elif max_punishment >= 10 * 365 and days_in_jail > 120:
                eligibility_conditions.append("2.2.7")
                bail_date = date_sent_to_jail + timedelta(days=120)


        # Condition 8
        if max_punishment <= 2 * 365:  # Assuming max_punishment is in days
            eligibility_conditions.append("2.2.8")

         # Condition 9
        if detained_under_crpc:
            eligibility_conditions.append("2.2.9")

        # Condition 10
        if sick_or_infirm:
            eligibility_conditions.append("2.2.10")


        # Condition 11
        if is_woman == "yes":
            eligibility_conditions.append("2.2.11")

        #Condition 12
        if (
            first_time_offender and
            age_between_19_and_21 == "yes" and
            max_punishment <= 7 * 365 and
            jail_duration_percentage >= 25
        ):
            eligibility_conditions.append("2.2.12")

        # Condition 13
        if unsound_mind:
            eligibility_conditions.append("2.2.13")

        #Condtion 14
        if chargesheet_filed:
            # If chargesheet is filed, check for the evidence date
            if (
                magistrate_trial and
                not bailable and
                not trial_concluded and
                first_date_fixed_for_evidence
            ):
                first_date_fixed_for_evidence = datetime.strptime(first_date_fixed_for_evidence, "%Y-%m-%d")
                current_date = datetime.now()

                # Calculate the difference in days
                days_have_elapsed = (current_date - first_date_fixed_for_evidence).days

                # Now you can use the `days_have_elapsed` variable in your condition
                if days_have_elapsed >= 60:
                    eligibility_conditions.append("2.2.14")


        if len(eligibility_conditions) == 0:
            result = f"{name} is not eligible for bail under any condition."
            return render_template("result.html", result=result)
        else:
            # Load guideline descriptions from Excel into a pandas DataFrame
            guidelines_data = pd.read_excel("/home/baileligibilitycalculator/UTRC/guidelines_data.xlsx")

            # Convert the DataFrame into a dictionary for easy access
            guideline_descriptions = dict(zip(
            guidelines_data['Guideline_Code'],
            guidelines_data['Guideline_Description']
            ))


            eligible_guidelines = [guideline_descriptions.get(guideline) for guideline in eligibility_conditions]
            eligible_guidelines = [guideline for guideline in eligible_guidelines if guideline is not None]  # Remove None values

            if eligible_guidelines:
                result = f"{name} is eligible for bail under the following Guidelines of NALSA:\n{''.join(eligible_guidelines)}"
            else:
                result = f"{name} is eligible for bail, but guideline descriptions are not available."

        return render_template("result.html", name=name, eligibility_conditions=eligibility_conditions, guideline_descriptions=guideline_descriptions, bail_date=bail_date, result=result)

    return render_template("input.html")


@app.route('/fetch_section_attributes', methods=['GET'])
def fetch_section_attributes():

    act = request.args.get("act")

    if act == "Gujarat Prohibition Act":

        sections = request.args.get("section").split(',')  # Split sections by comma
        max_punishment = 0
        bailable = "yes"
        compoundable = "yes"
        magistrate_trial = "yes"

        for section in sections:
            # Check if the section is purely an integer
            if section.isdigit():
                section_info = sections_data[sections_data["Sections"].astype(str) == f"{section}.0"]
            else:
                section_info = sections_data[sections_data["Sections"].astype(str) == section]

            if not section_info.empty:
                punishment = section_info.iloc[0, 1]
                bailable_condition = section_info.iloc[0, 2].lower() == "yes"
                compoundable_condition = section_info.iloc[0, 3].lower() == "yes"
                magistrate_trial_condition = section_info.iloc[0, 4].lower() == "yes"

                # Update max_punishment if the current section has a higher punishment
                if punishment > max_punishment:
                    max_punishment = punishment

                # Check conditions for bailable, compoundable, and magistrate_trial
                if not bailable_condition:
                    bailable = "no"
                if not compoundable_condition:
                    compoundable = "no"
                if not magistrate_trial_condition:
                    magistrate_trial = "no"
            else:
                # Handle the case when the section is not found in the Excel file
                return jsonify({"error": f"Section '{section}' not found in the data."})

        # Return the section attributes as JSON
        return jsonify({
            "max_punishment": max_punishment,
            "bailable": bailable,
            "compoundable": compoundable,
            "magistrate_trial": magistrate_trial,
        })

    elif act == "NDPS":

        sections = request.args.get("section").split(',')  # Split sections by comma
        max_punishment = 0
        bailable = "yes"
        compoundable = "yes"
        magistrate_trial = "yes"

        for section in sections:
            # Check if the section is purely an integer
            if section.isdigit():
                section_info = ndps_data[ndps_data["Sections"].astype(str) == f"{section}.0"]
            else:
                section_info = ndps_data[ndps_data["Sections"].astype(str) == section]

            if not section_info.empty:
                punishment = section_info.iloc[0, 1]
                bailable_condition = section_info.iloc[0, 2].lower() == "yes"
                compoundable_condition = section_info.iloc[0, 3].lower() == "yes"
                magistrate_trial_condition = section_info.iloc[0, 4].lower() == "yes"

                # Update max_punishment if the current section has a higher punishment
                if punishment > max_punishment:
                    max_punishment = punishment

                # Check conditions for bailable, compoundable, and magistrate_trial
                if not bailable_condition:
                    bailable = "no"
                if not compoundable_condition:
                    compoundable = "no"
                if not magistrate_trial_condition:
                    magistrate_trial = "no"
            else:
                # Handle the case when the section is not found in the Excel file
                return jsonify({"error": f"Section '{section}' not found in the data."})

        # Return the section attributes as JSON
        return jsonify({
            "max_punishment": max_punishment,
            "bailable": bailable,
            "compoundable": compoundable,
            "magistrate_trial": magistrate_trial,
        })



    elif act == "IPC":

        sections = request.args.get("section").split(',')  # Split sections by comma
        max_punishment = 0
        bailable = "yes"
        compoundable = "yes"
        magistrate_trial = "yes"

        for section in sections:
            # Check if the section is purely an integer
            if section.isdigit():
                section_info = ipc_data[ipc_data["Sections"].astype(str) == f"{section}.0"]
            else:
                section_info = ipc_data[ipc_data["Sections"].astype(str) == section]

            if not section_info.empty:
                punishment = section_info.iloc[0, 1]
                bailable_condition = section_info.iloc[0, 2].lower() == "yes"
                compoundable_condition = section_info.iloc[0, 3].lower() == "yes"
                magistrate_trial_condition = section_info.iloc[0, 4].lower() == "yes"

                # Update max_punishment if the current section has a higher punishment
                if punishment > max_punishment:
                    max_punishment = punishment

                # Check conditions for bailable, compoundable, and magistrate_trial
                if not bailable_condition:
                    bailable = "no"
                if not compoundable_condition:
                    compoundable = "no"
                if not magistrate_trial_condition:
                    magistrate_trial = "no"
            else:
                # Handle the case when the section is not found in the Excel file
                return jsonify({"error": f"Section '{section}' not found in the data."})

        # Return the section attributes as JSON
        return jsonify({
            "max_punishment": max_punishment,
            "bailable": bailable,
            "compoundable": compoundable,
            "magistrate_trial": magistrate_trial,
        })



    elif act == "POCSO":

        sections = request.args.get("section").split(',')  # Split sections by comma
        max_punishment = 0
        bailable = "yes"
        compoundable = "yes"
        magistrate_trial = "yes"

        for section in sections:
            # Check if the section is purely an integer
            if section.isdigit():
                section_info = pocso_data[pocso_data["Sections"].astype(str) == f"{section}.0"]
            else:
                section_info = pocso_data[pocso_data["Sections"].astype(str) == section]

            if not section_info.empty:
                punishment = section_info.iloc[0, 1]
                bailable_condition = section_info.iloc[0, 2].lower() == "yes"
                compoundable_condition = section_info.iloc[0, 3].lower() == "yes"
                magistrate_trial_condition = section_info.iloc[0, 4].lower() == "yes"

                # Update max_punishment if the current section has a higher punishment
                if punishment > max_punishment:
                    max_punishment = punishment

                # Check conditions for bailable, compoundable, and magistrate_trial
                if not bailable_condition:
                    bailable = "no"
                if not compoundable_condition:
                    compoundable = "no"
                if not magistrate_trial_condition:
                    magistrate_trial = "no"
            else:
                # Handle the case when the section is not found in the Excel file
                return jsonify({"error": f"Section '{section}' not found in the data."})

        # Return the section attributes as JSON
        return jsonify({
            "max_punishment": max_punishment,
            "bailable": bailable,
            "compoundable": compoundable,
            "magistrate_trial": magistrate_trial,
        })


# for 2nd Act
@app.route('/fetch_section_attributes1', methods=['GET'])
def fetch_section_attributes1():

    act = request.args.get("act1")

    if act == "Gujarat Prohibition Act":

        sections = request.args.get("section1").split(',')  # Split sections by comma
        max_punishment = 0
        bailable = "yes"
        compoundable = "yes"
        magistrate_trial = "yes"

        for section in sections:
            # Check if the section is purely an integer
            if section.isdigit():
                section_info = sections_data[sections_data["Sections"].astype(str) == f"{section}.0"]
            else:
                section_info = sections_data[sections_data["Sections"].astype(str) == section]

            if not section_info.empty:
                punishment = section_info.iloc[0, 1]
                bailable_condition = section_info.iloc[0, 2].lower() == "yes"
                compoundable_condition = section_info.iloc[0, 3].lower() == "yes"
                magistrate_trial_condition = section_info.iloc[0, 4].lower() == "yes"

                # Update max_punishment if the current section has a higher punishment
                if punishment > max_punishment:
                    max_punishment = punishment

                # Check conditions for bailable, compoundable, and magistrate_trial
                if not bailable_condition:
                    bailable = "no"
                if not compoundable_condition:
                    compoundable = "no"
                if not magistrate_trial_condition:
                    magistrate_trial = "no"
            else:
                # Handle the case when the section is not found in the Excel file
                return jsonify({"error": f"Section '{section}' not found in the data."})

        # Return the section attributes as JSON
        return jsonify({
            "max_punishment": max_punishment,
            "bailable": bailable,
            "compoundable": compoundable,
            "magistrate_trial": magistrate_trial,
        })

    elif act == "NDPS":

        sections = request.args.get("section1").split(',')  # Split sections by comma
        max_punishment = 0
        bailable = "yes"
        compoundable = "yes"
        magistrate_trial = "yes"

        for section in sections:
            # Check if the section is purely an integer
            if section.isdigit():
                section_info = ndps_data[ndps_data["Sections"].astype(str) == f"{section}.0"]
            else:
                section_info = ndps_data[ndps_data["Sections"].astype(str) == section]

            if not section_info.empty:
                punishment = section_info.iloc[0, 1]
                bailable_condition = section_info.iloc[0, 2].lower() == "yes"
                compoundable_condition = section_info.iloc[0, 3].lower() == "yes"
                magistrate_trial_condition = section_info.iloc[0, 4].lower() == "yes"

                # Update max_punishment if the current section has a higher punishment
                if punishment > max_punishment:
                    max_punishment = punishment

                # Check conditions for bailable, compoundable, and magistrate_trial
                if not bailable_condition:
                    bailable = "no"
                if not compoundable_condition:
                    compoundable = "no"
                if not magistrate_trial_condition:
                    magistrate_trial = "no"
            else:
                # Handle the case when the section is not found in the Excel file
                return jsonify({"error": f"Section '{section}' not found in the data."})

        # Return the section attributes as JSON
        return jsonify({
            "max_punishment": max_punishment,
            "bailable": bailable,
            "compoundable": compoundable,
            "magistrate_trial": magistrate_trial,
        })



    elif act == "IPC":

        sections = request.args.get("section1").split(',')  # Split sections by comma
        max_punishment = 0
        bailable = "yes"
        compoundable = "yes"
        magistrate_trial = "yes"

        for section in sections:
            # Check if the section is purely an integer
            if section.isdigit():
                section_info = ipc_data[ipc_data["Sections"].astype(str) == f"{section}.0"]
            else:
                section_info = ipc_data[ipc_data["Sections"].astype(str) == section]

            if not section_info.empty:
                punishment = section_info.iloc[0, 1]
                bailable_condition = section_info.iloc[0, 2].lower() == "yes"
                compoundable_condition = section_info.iloc[0, 3].lower() == "yes"
                magistrate_trial_condition = section_info.iloc[0, 4].lower() == "yes"

                # Update max_punishment if the current section has a higher punishment
                if punishment > max_punishment:
                    max_punishment = punishment

                # Check conditions for bailable, compoundable, and magistrate_trial
                if not bailable_condition:
                    bailable = "no"
                if not compoundable_condition:
                    compoundable = "no"
                if not magistrate_trial_condition:
                    magistrate_trial = "no"
            else:
                # Handle the case when the section is not found in the Excel file
                return jsonify({"error": f"Section '{section}' not found in the data."})

        # Return the section attributes as JSON
        return jsonify({
            "max_punishment": max_punishment,
            "bailable": bailable,
            "compoundable": compoundable,
            "magistrate_trial": magistrate_trial,
        })



    elif act == "POCSO":

        sections = request.args.get("section1").split(',')  # Split sections by comma
        max_punishment = 0
        bailable = "yes"
        compoundable = "yes"
        magistrate_trial = "yes"

        for section in sections:

            # Check if the section is purely an integer
            if section.isdigit():
                section_info = pocso_data[pocso_data["Sections"].astype(str) == f"{section}.0"]
            else:
                section_info = pocso_data[pocso_data["Sections"].astype(str) == section]

            if not section_info.empty:
                punishment = section_info.iloc[0, 1]
                bailable_condition = section_info.iloc[0, 2].lower() == "yes"
                compoundable_condition = section_info.iloc[0, 3].lower() == "yes"
                magistrate_trial_condition = section_info.iloc[0, 4].lower() == "yes"

                # Update max_punishment if the current section has a higher punishment
                if punishment > max_punishment:
                    max_punishment = punishment

                # Check conditions for bailable, compoundable, and magistrate_trial
                if not bailable_condition:
                    bailable = "no"
                if not compoundable_condition:
                    compoundable = "no"
                if not magistrate_trial_condition:
                    magistrate_trial = "no"
            else:
                # Handle the case when the section is not found in the Excel file
                return jsonify({"error": f"Section '{section}' not found in the data."})

        # Return the section attributes as JSON
        return jsonify({
            "max_punishment": max_punishment,
            "bailable": bailable,
            "compoundable": compoundable,
            "magistrate_trial": magistrate_trial,
        })

# for 3rd Act
@app.route('/fetch_section_attributes2', methods=['GET'])
def fetch_section_attributes2():

    act = request.args.get("act2")

    if act == "Gujarat Prohibition Act":

        sections = request.args.get("section2").split(',')  # Split sections by comma
        max_punishment = 0
        bailable = "yes"
        compoundable = "yes"
        magistrate_trial = "yes"

        for section in sections:
            # Check if the section is purely an integer
            if section.isdigit():
                section_info = sections_data[sections_data["Sections"].astype(str) == f"{section}.0"]
            else:
                section_info = sections_data[sections_data["Sections"].astype(str) == section]

            if not section_info.empty:
                punishment = section_info.iloc[0, 1]
                bailable_condition = section_info.iloc[0, 2].lower() == "yes"
                compoundable_condition = section_info.iloc[0, 3].lower() == "yes"
                magistrate_trial_condition = section_info.iloc[0, 4].lower() == "yes"

                # Update max_punishment if the current section has a higher punishment
                if punishment > max_punishment:
                    max_punishment = punishment

                # Check conditions for bailable, compoundable, and magistrate_trial
                if not bailable_condition:
                    bailable = "no"
                if not compoundable_condition:
                    compoundable = "no"
                if not magistrate_trial_condition:
                    magistrate_trial = "no"
            else:
                # Handle the case when the section is not found in the Excel file
                return jsonify({"error": f"Section '{section}' not found in the data."})

        # Return the section attributes as JSON
        return jsonify({
            "max_punishment": max_punishment,
            "bailable": bailable,
            "compoundable": compoundable,
            "magistrate_trial": magistrate_trial,
        })

    elif act == "NDPS":

        sections = request.args.get("section2").split(',')  # Split sections by comma
        max_punishment = 0
        bailable = "yes"
        compoundable = "yes"
        magistrate_trial = "yes"

        for section in sections:
            # Check if the section is purely an integer
            if section.isdigit():
                section_info = ndps_data[ndps_data["Sections"].astype(str) == f"{section}.0"]
            else:
                section_info = ndps_data[ndps_data["Sections"].astype(str) == section]

            if not section_info.empty:
                punishment = section_info.iloc[0, 1]
                bailable_condition = section_info.iloc[0, 2].lower() == "yes"
                compoundable_condition = section_info.iloc[0, 3].lower() == "yes"
                magistrate_trial_condition = section_info.iloc[0, 4].lower() == "yes"

                # Update max_punishment if the current section has a higher punishment
                if punishment > max_punishment:
                    max_punishment = punishment

                # Check conditions for bailable, compoundable, and magistrate_trial
                if not bailable_condition:
                    bailable = "no"
                if not compoundable_condition:
                    compoundable = "no"
                if not magistrate_trial_condition:
                    magistrate_trial = "no"
            else:
                # Handle the case when the section is not found in the Excel file
                return jsonify({"error": f"Section '{section}' not found in the data."})

        # Return the section attributes as JSON
        return jsonify({
            "max_punishment": max_punishment,
            "bailable": bailable,
            "compoundable": compoundable,
            "magistrate_trial": magistrate_trial,
        })



    elif act == "IPC":

        sections = request.args.get("section2").split(',')  # Split sections by comma
        max_punishment = 0
        bailable = "yes"
        compoundable = "yes"
        magistrate_trial = "yes"

        for section in sections:
            # Check if the section is purely an integer
            if section.isdigit():
                section_info = ipc_data[ipc_data["Sections"].astype(str) == f"{section}.0"]
            else:
                section_info = ipc_data[ipc_data["Sections"].astype(str) == section]

            if not section_info.empty:
                punishment = section_info.iloc[0, 1]
                bailable_condition = section_info.iloc[0, 2].lower() == "yes"
                compoundable_condition = section_info.iloc[0, 3].lower() == "yes"
                magistrate_trial_condition = section_info.iloc[0, 4].lower() == "yes"

                # Update max_punishment if the current section has a higher punishment
                if punishment > max_punishment:
                    max_punishment = punishment

                # Check conditions for bailable, compoundable, and magistrate_trial
                if not bailable_condition:
                    bailable = "no"
                if not compoundable_condition:
                    compoundable = "no"
                if not magistrate_trial_condition:
                    magistrate_trial = "no"
            else:
                # Handle the case when the section is not found in the Excel file
                return jsonify({"error": f"Section '{section}' not found in the data."})

        # Return the section attributes as JSON
        return jsonify({
            "max_punishment": max_punishment,
            "bailable": bailable,
            "compoundable": compoundable,
            "magistrate_trial": magistrate_trial,
        })



    elif act == "POCSO":

        sections = request.args.get("section2").split(',')  # Split sections by comma
        max_punishment = 0
        bailable = "yes"
        compoundable = "yes"
        magistrate_trial = "yes"
        #non_bailable = ["4(1)","4(2)","6(1)","8","10","12","14(1)","14(2)","15(2)","15(3)"]

        for section in sections:
            # Check if the section is purely an integer
            if section.isdigit():
                section_info = pocso_data[pocso_data["Sections"].astype(str) == f"{section}.0"]
            else:
                section_info = pocso_data[pocso_data["Sections"].astype(str) == section]

            if not section_info.empty:
                punishment = section_info.iloc[0, 1]
                bailable_condition = section_info.iloc[0, 2].lower() == "yes"
                compoundable_condition = section_info.iloc[0, 3].lower() == "yes"
                magistrate_trial_condition = section_info.iloc[0, 4].lower() == "yes"

                # Update max_punishment if the current section has a higher punishment
                if punishment > max_punishment:
                    max_punishment = punishment

                # Check conditions for bailable, compoundable, and magistrate_trial
                if not bailable_condition:
                    bailable = "no"
                if not compoundable_condition:
                    compoundable = "no"
                if not magistrate_trial_condition:
                    magistrate_trial = "no"
                #if section in non_bailable:
                #    bailable = "working"
                #else:
                #    bailable = "working1"

            else:
                # Handle the case when the section is not found in the Excel file
                return jsonify({"error": f"Section '{section}' not found in the data."})

        # Return the section attributes as JSON
        return jsonify({
            "max_punishment": max_punishment,
            "bailable": bailable,
            "compoundable": compoundable,
            "magistrate_trial": magistrate_trial,
        })



#if __name__ == "__main__":
    #app.run(debug=True)
