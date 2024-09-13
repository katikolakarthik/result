from flask import Flask, render_template, request, jsonify
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Store the dataframe globally to access after file upload
df = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global df
    file = request.files['file']
    
    # Check if the file is an Excel file
    if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
        # Load the Excel data dynamically
        df = pd.read_excel(file)
        subjects = df['Sub Name'].unique()
        return jsonify({'subjects': list(subjects)})
    else:
        return jsonify({'error': 'Invalid file type. Please upload an Excel file.'}), 400

@app.route('/get_stats', methods=['POST'])
def get_stats():
    global df
    if df is None:
        return jsonify({'error': 'No data uploaded yet.'}), 400
    
    # Get the subject name from the request
    subject_name = request.form['subject_name']
    
    # Filter data for the selected subject
    subject_data = df[df['Sub Name'] == subject_name]

    # Calculate pass/fail stats
    num_students_fail = subject_data[subject_data['Status'] == 'FAIL'].shape[0]
    num_students_pass = subject_data[subject_data['Status'] == 'PASS'].shape[0]
    total_students = subject_data.shape[0]
    
    fail_percentage = (num_students_fail / total_students) * 100
    pass_percentage = (num_students_pass / total_students) * 100

    # Find students with highest and lowest total marks
    highest_marks = subject_data['Total'].max()
    lowest_marks = subject_data['Total'].min()

    highest_students = subject_data[subject_data['Total'] == highest_marks]
    lowest_students = subject_data[subject_data['Total'] == lowest_marks]

    highest_students_info = highest_students[['Name', 'Total']]
    lowest_students_info = lowest_students[['Name', 'Total']]

    # Create the pie or bar chart based on user choice
    chart_type = request.form.get('chart_type', 'pie')

    fig, ax = plt.subplots(figsize=(6, 3))

    if chart_type == 'bar':
        ax.bar(['Pass', 'Fail'], [pass_percentage, fail_percentage], color=['green', 'red'])
        plt.title(f'Pass/Fail Percentage for {subject_name}')
    else:  # Default to pie chart
        ax.pie([pass_percentage, fail_percentage], labels=['Pass', 'Fail'], autopct='%1.1f%%', startangle=140)
        plt.title(f'Pass/Fail Percentage for {subject_name}')
    
    # Save the plot as a PNG image in memory
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')

    # Return the stats, chart, and student information
    return jsonify({
        'pass_percentage': pass_percentage,
        'fail_percentage': fail_percentage,
        'num_students_pass': num_students_pass,
        'num_students_fail': num_students_fail,
        'plot_url': plot_url,
        'highest_students': highest_students_info.to_dict(orient='records'),
        'lowest_students': lowest_students_info.to_dict(orient='records')
    })

if __name__ == '__main__':
    app.run(debug=True)
