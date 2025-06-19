import pymysql
from datetime import datetime

# Function to create the hospital database
def create_database():
    conn = pymysql.connect(host='localhost', user='root', password='Sunita@29')
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS hospital")
    conn.commit()
    conn.close()

def connect_db():
    return pymysql.connect(host='localhost', user='root', password='Sunita@29', database='hospital')

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Doctor table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Doctor (
        Doctor_ID VARCHAR(10) PRIMARY KEY,
        Name VARCHAR(100) NOT NULL,
        Specialization VARCHAR(100),
        Fee DECIMAL(10,2) DEFAULT 500.00,
        Contact VARCHAR(10) CHECK (LENGTH(Contact) = 10),
        Department VARCHAR(100),
        Qualification VARCHAR(100),
        Date_of_Joining DATE,
        Experience INT)''')

    # Check/Add Fee column
    cursor.execute('''SELECT COUNT(*) FROM information_schema.COLUMNS 
                   WHERE TABLE_SCHEMA = 'hospital' 
                   AND TABLE_NAME = 'Doctor' 
                   AND COLUMN_NAME = 'Fee' ''')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''ALTER TABLE Doctor ADD COLUMN Fee DECIMAL(10,2) DEFAULT 500.00''')

    # Patient table with Disease and Doctor_ID
    cursor.execute('''CREATE TABLE IF NOT EXISTS Patient (
        Patient_ID VARCHAR(10) PRIMARY KEY,
        Name VARCHAR(100) NOT NULL,
        Age INT CHECK (Age > 0),
        Gender VARCHAR(10),
        Address TEXT,
        Contact VARCHAR(10) CHECK (LENGTH(Contact) = 10),
        Blood_Type VARCHAR(5),
        Emergency_Contact VARCHAR(10) CHECK (LENGTH(Emergency_Contact) = 10),
        Insurance_Details TEXT,
        Disease VARCHAR(100),
        Doctor_ID VARCHAR(10),
        FOREIGN KEY (Doctor_ID) REFERENCES Doctor(Doctor_ID))''')

    # Check/Add Disease & Doctor_ID columns
    for column in ['Disease', 'Doctor_ID']:
        cursor.execute(f'''SELECT COUNT(*) FROM information_schema.COLUMNS 
                       WHERE TABLE_SCHEMA = 'hospital' 
                       AND TABLE_NAME = 'Patient' 
                       AND COLUMN_NAME = '{column}' ''')
        if cursor.fetchone()[0] == 0:
            dtype = 'VARCHAR(100)' if column == 'Disease' else 'INT'
            cursor.execute(f'''ALTER TABLE Patient ADD COLUMN {column} {dtype}''')
  # Removed_Patients table (new)
    cursor.execute('''CREATE TABLE IF NOT EXISTS Removed_Patients (
        Patient_ID VARCHAR(10) PRIMARY KEY,  # Changed to VARCHAR
        Name VARCHAR(100) NOT NULL,
        Age INT,
        Gender VARCHAR(10),
        Address TEXT,
        Contact VARCHAR(10),
        Blood_Type VARCHAR(5),
        Emergency_Contact VARCHAR(10),
        Insurance_Details TEXT,
        Disease VARCHAR(100),
        Doctor_ID VARCHAR(10),  # Changed to VARCHAR
        Removal_Date DATE)''')  
# Removed_Doctors table (new)
    cursor.execute('''CREATE TABLE IF NOT EXISTS Removed_Doctors (
        Doctor_ID VARCHAR(10) PRIMARY KEY,  # Changed to VARCHAR
        Name VARCHAR(100) NOT NULL,
        Specialization VARCHAR(100),
        Fee DECIMAL(10,2),
        Contact VARCHAR(10),
        Department VARCHAR(100),
        Qualification VARCHAR(100),
        Date_of_Joining DATE,
        Experience INT,
        Removal_Date DATE)''')

    # Room Allocation table
    # Room Allocation table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Room_Allocation (
    Room_ID INT AUTO_INCREMENT PRIMARY KEY,
    Room_Number INT CHECK (Room_Number BETWEEN 1 AND 10),
    Patient_ID VARCHAR(10),  # Removed UNIQUE constraint
    Admission_Date DATE,
    Discharge_Date DATE DEFAULT NULL,
    FOREIGN KEY (Patient_ID) REFERENCES Patient(Patient_ID))''')

    # Billing table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Billing (
        Bill_ID INT AUTO_INCREMENT PRIMARY KEY,
        Patient_ID VARCHAR(10),  # Changed to VARCHAR
        Room_Charges DECIMAL(10,2),
        Doctor_Fees DECIMAL(10,2),
        Total_Amount DECIMAL(10,2),
        Payment_Status VARCHAR(20) DEFAULT 'Pending',
        FOREIGN KEY (Patient_ID) REFERENCES Patient(Patient_ID))''')

    conn.commit()
    conn.close()

# ==================== PATIENT FUNCTIONS ====================
def generate_doctor_id():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(Doctor_ID) FROM Doctor")
    max_id = cursor.fetchone()[0]
    conn.close()
    if not max_id:  # If no doctors exist yet
        return "D1"
    numeric_part = int(max_id[1:]) + 1  # Extract number and increment
    return f"D{numeric_part}"

def generate_patient_id():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(Patient_ID) FROM Patient")
    max_id = cursor.fetchone()[0]
    conn.close()
    if not max_id:  # If no patients exist yet
        return "P1"
    numeric_part = int(max_id[1:]) + 1  # Extract number and increment
    return f"P{numeric_part}"

def register_patient():
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n-- New Patient Registration --")
    
    # Automatically generate Patient ID (P1, P2, etc.)
    patient_id = generate_patient_id()
    
    # Collect patient details
    details = [
        patient_id,  # Add generated ID
        input("Full Name: ").strip(),
        int(input("Age: ")),
        input("Gender: ").strip(),
        input("Address: ").strip(),
        input("Contact (10 digits): ").strip(),
        input("Blood Type: ").strip().upper(),
        input("Emergency Contact (10 digits): ").strip(),
        input("Insurance Details: ").strip(),
        input("Medical Condition/Disease: ").strip().lower()
    ]
    
    disease = details[-1]
    
    # Assign a doctor (if available)
    cursor.execute('''SELECT d.Doctor_ID, d.Fee 
                   FROM Doctor d
                   LEFT JOIN Patient p ON d.Doctor_ID = p.Doctor_ID
                   WHERE LOWER(d.Specialization) = %s
                   GROUP BY d.Doctor_ID
                   HAVING COUNT(p.Patient_ID) < 3
                   ORDER BY d.Experience DESC
                   LIMIT 1''', (disease,))
    doctor = cursor.fetchone()
    
    # Insert patient with or without doctor
    cursor.execute('''INSERT INTO Patient 
        (Patient_ID, Name, Age, Gender, Address, Contact, Blood_Type, 
         Emergency_Contact, Insurance_Details, Disease, Doctor_ID)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
        details + [doctor[0] if doctor else None])  # Add Doctor_ID if available
    
    if doctor:
        print(f"Doctor {doctor[0]} assigned successfully!")
    else:
        print(f"! No doctor found for '{disease}'. Will auto-assign later.")

    # Room allocation
    if input("Require hospitalization? (yes/no): ").lower() == 'yes':
        cursor.execute('''SELECT Room_Number FROM (
            SELECT Room_Number, COUNT(Patient_ID) as occupants 
            FROM Room_Allocation 
            WHERE Discharge_Date IS NULL
            GROUP BY Room_Number
            HAVING occupants < 5
        ) AS available_rooms LIMIT 1''')
        
        room = cursor.fetchone()
        room_number = room[0] if room else None
        
        if not room_number:
            cursor.execute("SELECT COALESCE(MAX(Room_Number), 0) FROM Room_Allocation")
            room_number = cursor.fetchone()[0] + 1
        
        date_choice = input("Use today's date? (yes/no): ").lower()
        admission_date = datetime.now().date() if date_choice == 'yes' else input("Enter date (YYYY-MM-DD): ")
        
        cursor.execute('''INSERT INTO Room_Allocation 
                       (Room_Number, Patient_ID, Admission_Date)
                       VALUES (%s, %s, %s)''', 
                       (room_number, patient_id, admission_date))

    conn.commit()
    print(f"Patient registered! ID: {patient_id}")
    conn.close()


def drop_all_tables():
    conn = connect_db()
    cursor = conn.cursor()
    
    # List of all tables in your database
    tables = [
        "Billing",
        "Room_Allocation",
        "Patient",
        "Doctor",
        "Removed_Patients",
        "Removed_Doctors"
    ]
    
    # Drop each table
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"✅ Dropped table: {table}")
        except Exception as e:
            print(f"❌ Error dropping table {table}: {e}")
    
    conn.commit()
    conn.close()
    

def get_patient_id():
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n-- Retrieve Patient ID --")
    name = input("Enter your full name: ")
    contact = input("Enter your contact number: ")
    
    cursor.execute('''SELECT Patient_ID FROM Patient 
                   WHERE Name = %s AND Contact = %s''', (name, contact))
    result = cursor.fetchone()
    print(f"\nYour Patient ID: {result[0]}") if result else print("\nPatient not found!")
    conn.close()

def view_patient_doctor():
    conn = connect_db()
    cursor = conn.cursor()
    
    patient_id = input("\nEnter Patient ID: ")
    cursor.execute('''SELECT d.Doctor_ID, d.Name, d.Specialization, d.Contact 
                   FROM Patient p
                   JOIN Doctor d ON p.Doctor_ID = d.Doctor_ID
                   WHERE p.Patient_ID = %s''', (patient_id,))
    
    doctors = cursor.fetchall()
    if doctors:
        print("\nYour Doctors:")
        for doc in doctors:
            print(f"ID: {doc[0]} | Name: {doc[1]} | Specialty: {doc[2]} | Contact: {doc[3]}")
    else:
        print("\nNo doctors allocated!")
    conn.close()

def view_patient_room():
    conn = connect_db()
    cursor = conn.cursor()
    
    patient_id = input("\nEnter Patient ID: ")
    cursor.execute('''SELECT Room_Number, Admission_Date 
                   FROM Room_Allocation WHERE Patient_ID = %s''', (patient_id,))
    
    room = cursor.fetchone()
    if room:
        print(f"\nRoom: {room[0]} | Admission Date: {room[1]}")
    else:
        print("\nNo room allocated!")
    conn.close()

def patient_discharge():
    conn = connect_db()
    cursor = conn.cursor()
    
    patient_id = input("Enter Patient ID: ")

    # Validate patient exists
    cursor.execute('''SELECT * FROM Patient WHERE Patient_ID = %s''', (patient_id,))
    if not cursor.fetchone():
        print("\nError: Invalid Patient ID!")
        conn.close()
        return

    # Check doctor assignment
    cursor.execute('''SELECT Doctor_ID FROM Patient WHERE Patient_ID = %s''', (patient_id,))
    doctor_result = cursor.fetchone()
    has_doctor = doctor_result and doctor_result[0] is not None

    # Check room allocation
    cursor.execute('''SELECT Admission_Date FROM Room_Allocation 
                   WHERE Patient_ID = %s AND Discharge_Date IS NULL''', (patient_id,))
    room_result = cursor.fetchone()

    room_charge = 0
    doctor_fee = 0
    discharge_date = None
    days_stayed = 0

    # Room handling
    if room_result:
        cursor.execute('''UPDATE Room_Allocation 
                        SET Discharge_Date = %s 
                        WHERE Patient_ID = %s 
                        AND Discharge_Date IS NULL''',  # Ensure only active room is discharged
                        (discharge_date, patient_id))
        admission_date = room_result[0]
        while True:
            try:
                discharge_date = input("Enter discharge date (YYYY-MM-DD): ")
                admission = datetime.strptime(str(admission_date), "%Y-%m-%d")
                discharge = datetime.strptime(discharge_date, "%Y-%m-%d")
                
                if discharge < admission:
                    print("Error: Discharge date cannot be before admission!")
                    continue
                    
                days_stayed = (discharge - admission).days + 1
                room_charge = days_stayed * 500  # Fixed ₹500 per day
                break
            except ValueError:
                print("Invalid date format! Use YYYY-MM-DD")

    # Doctor handling
    if has_doctor:
        cursor.execute('''SELECT Fee FROM Doctor WHERE Doctor_ID = %s''', (doctor_result[0],))
        doctor_fee = cursor.fetchone()[0]
    else:
        confirm = input("\nWARNING: No doctor assigned! Discharge without treatment? (yes/no): ").lower()
        if confirm != 'yes':
            print("Discharge cancelled!")
            conn.close()
            return

    total = room_charge + doctor_fee

    # Show bill FIRST
    print("\n=== BILL SUMMARY ===")
    if room_result:
        print(f"Room Charges ({days_stayed} days × ₹500): ₹{room_charge}")
    if has_doctor:
        print(f"Doctor Fees: ₹{doctor_fee}")
    print(f"Total Amount: ₹{total}")

    # Payment handling AFTER showing bill
    payment_status = 'Paid'
    payment_message = ""
    
    if total > 0:
        payment = input("\nHas the payment been made? (yes/no): ").lower()
        payment_status = 'Paid' if payment == 'yes' else 'Pending'
        if payment_status == 'Pending':
            payment_message = "\nNOTE: Please clear dues at billing counter within 3 days!"
    else:
        payment_status = 'Free'
        payment_message = "\nNo charges applicable - free discharge!"

    # Update records
    cursor.execute('''INSERT INTO Billing 
                   (Patient_ID, Room_Charges, Doctor_Fees, Total_Amount, Payment_Status)
                   VALUES (%s, %s, %s, %s, %s)''', 
                   (patient_id, room_charge, doctor_fee, total, payment_status))

    if room_result:
        cursor.execute('''UPDATE Room_Allocation 
                       SET Discharge_Date = %s 
                       WHERE Patient_ID = %s''', (discharge_date, patient_id))

    conn.commit()
    print(f"\n✅ Discharge successful! {payment_message}")
    conn.close()
# ==================== DOCTOR FUNCTIONS ====================
def register_doctor():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Automatically generate Doctor ID (D1, D2, etc.)
    doctor_id = generate_doctor_id()
    
    # Collect doctor details
    details = [
        doctor_id,  # Add generated ID
        input("Full Name: ").strip(),
        input("Specialization: ").strip().lower(),
        float(input("Consultation Fee: ")),
        input("Contact (10 digits): ").strip(),
        input("Department: ").strip(),
        input("Qualification: ").strip(),
        input("Date of Joining (YYYY-MM-DD): ").strip(),
        int(input("Years of Experience: "))
    ]
    
    # Insert doctor into database
    cursor.execute('''INSERT INTO Doctor 
        (Doctor_ID, Name, Specialization, Fee, Contact, Department, 
         Qualification, Date_of_Joining, Experience)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''', details)
    
    # Auto-assign up to 3 patients with matching conditions
    specialization = details[2]  # Specialization is at index 2
    cursor.execute('''UPDATE Patient 
                   SET Doctor_ID = %s 
                   WHERE LOWER(Disease) = %s 
                   AND Doctor_ID IS NULL
                   LIMIT 3''', (doctor_id, specialization))
    
    conn.commit()
    print(f"\nDoctor registered! ID: {doctor_id}")
    print(f"Auto-assigned to {cursor.rowcount} patients.")
    conn.close()

def view_removed_doctors():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            Doctor_ID, 
            Name, 
            Specialization, 
            Removal_Date 
        FROM Removed_Doctors
        ORDER BY Removal_Date DESC
    ''')
    
    removed_doctors = cursor.fetchall()
    
    if removed_doctors:
        print("\n=== Removed Doctors ===")
        print("ID | Name | Specialization | Removal Date")
        print("-" * 50)
        for doc in removed_doctors:
            print(f"{doc[0]} | {doc[1]} | {doc[2]} | {doc[3]}")
    else:
        print("\nNo removed doctors found!")
    
    conn.close()


def view_removed_patients():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            Patient_ID, 
            Name, 
            Disease, 
            Removal_Date 
        FROM Removed_Patients
        ORDER BY Removal_Date DESC
    ''')
    
    removed_patients = cursor.fetchall()
    
    if removed_patients:
        print("\n=== Removed Patients ===")
        print("ID | Name | Disease | Removal Date")
        print("-" * 50)
        for p in removed_patients:
            print(f"{p[0]} | {p[1]} | {p[2]} | {p[3]}")
    else:
        print("\nNo removed patients found!")
    
    conn.close()
    

def get_doctor_id():
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n-- Retrieve Doctor ID --")
    name = input("Enter your full name: ")
    contact = input("Enter your contact number: ")
    
    cursor.execute('''SELECT Doctor_ID FROM Doctor 
                   WHERE Name = %s AND Contact = %s''', (name, contact))
    result = cursor.fetchone()
    print(f"\nYour Doctor ID: {result[0]}") if result else print("\nDoctor not found!")
    conn.close()

def view_doctor_patients():
    conn = connect_db()
    cursor = conn.cursor()
    
    doctor_id = input("\nEnter Doctor ID: ")
    cursor.execute('''SELECT Patient_ID, Name, Age, Gender 
                   FROM Patient 
                   WHERE Doctor_ID = %s''', (doctor_id,))
    
    patients = cursor.fetchall()
    if patients:
        print("\nYour Patients:")
        for pat in patients:
            print(f"ID: {pat[0]} | Name: {pat[1]} | Age: {pat[2]} | Gender: {pat[3]}")
    else:
        print("\nNo patients allocated!")
    conn.close()

# ==================== ADMIN FUNCTIONS ====================
def view_all_patients():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            p.Patient_ID, p.Name, p.Age, p.Gender, p.Contact, 
            p.Blood_Type, p.Disease,
            d.Name AS Doctor_Name, d.Specialization AS Doctor_Specialization,
            ra.Room_Number, ra.Admission_Date, ra.Discharge_Date,
            CASE 
                WHEN ra.Discharge_Date IS NULL THEN 'In Hospital'
                ELSE 'Discharged'
            END AS Status
        FROM Patient p
        LEFT JOIN Doctor d ON p.Doctor_ID = d.Doctor_ID
        LEFT JOIN Room_Allocation ra ON p.Patient_ID = ra.Patient_ID
        ORDER BY CAST(SUBSTRING(p.Patient_ID, 2) AS UNSIGNED)  -- Numerical sorting
    ''')
    # ... rest of the code ...
    
    patients = cursor.fetchall()
    
    if patients:
        print("\n=== All Patients ===")
        print("ID | Name | Age | Gender | Contact | Blood Type | Disease | Doctor | Specialization | Room | Admission Date | Discharge Date | Status")
        print("-" * 120)
        for p in patients:
            print(f"{p[0]} | {p[1]} | {p[2]} | {p[3]} | {p[4]} | {p[5]} | {p[6]} | {p[7] or 'Not Assigned'} | {p[8] or 'N/A'} | {p[9] or 'N/A'} | {p[10] or 'N/A'} | {p[11] or 'N/A'} | {p[12]}")
    else:
        print("\nNo patients found!")
    
    conn.close()

def view_all_doctors():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            d.Doctor_ID, d.Name, d.Specialization, d.Fee, d.Contact, 
            d.Department, d.Qualification, d.Date_of_Joining, d.Experience,
            COUNT(p.Patient_ID) AS Patient_Count
        FROM Doctor d
        LEFT JOIN Patient p ON d.Doctor_ID = p.Doctor_ID
        GROUP BY d.Doctor_ID
        ORDER BY CAST(SUBSTRING(d.Doctor_ID, 2) AS UNSIGNED)  -- Numerical sorting
    ''')
    
    doctors = cursor.fetchall()
    
    if doctors:
        print("\n=== All Doctors ===")
        print("ID | Name | Specialization | Fee | Contact | Department | Qualification | Date of Joining | Experience | Patients Assigned")
        print("-" * 120)
        for d in doctors:
            print(f"{d[0]} | {d[1]} | {d[2]} | ₹{d[3]} | {d[4]} | {d[5]} | {d[6]} | {d[7]} | {d[8]} years | {d[9]}")
    else:
        print("\nNo doctors found!")
    
    conn.close()

def view_allocated_rooms():
    conn = connect_db()
    cursor = conn.cursor()
    
    # ========== UPDATED CODE: SHOW STATUS BASED ON DISCHARGE DATE ==========
    cursor.execute('''SELECT 
        Room_Number, 
        Patient_ID, 
        Admission_Date, 
        Discharge_Date,
        CASE 
            WHEN Discharge_Date IS NULL THEN 'Occupied' 
            ELSE 'Vacant' 
        END AS Status
        FROM Room_Allocation''')
    # =======================================================================
    
    print("\nRoom Allocations:")
    for r in cursor.fetchall():
        print(f"Room {r[0]} | Patient {r[1]} | {r[4]} | Admission: {r[2]}")
    
    conn.close()

def view_available_doctors():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            d.Doctor_ID, 
            d.Name, 
            d.Specialization,
            3 - COUNT(p.Patient_ID) AS Available_Slots
        FROM Doctor d
        LEFT JOIN Patient p ON d.Doctor_ID = p.Doctor_ID
        GROUP BY d.Doctor_ID
        HAVING Available_Slots > 0
        ORDER BY CAST(SUBSTRING(d.Doctor_ID, 2) AS UNSIGNED)
    ''')
    
    available_doctors = cursor.fetchall()
    
    if available_doctors:
        print("\n=== Available Doctors ===")
        print("ID | Name | Specialization | Available Slots")
        print("-" * 50)
        for doc in available_doctors:
            print(f"{doc[0]} | {doc[1]} | {doc[2]} | {doc[3]}")
    else:
        print("\nNo available doctors found!")
    
    conn.close()

def add_sample_data():
    conn = connect_db()
    cursor = conn.cursor()

    # Add 5 Doctors (Indian Names)
    doctors = [
        ("D1", "Dr. Rajesh Sharma", "Cardiology", 1000, "9876543210", "Heart", "MD", "2023-01-01", 10),
        ("D2", "Dr. Priya Singh", "Endocrinology", 800, "8765432109", "Diabetes", "MD", "2023-02-01", 8),
        ("D3", "Dr. Anil Gupta", "Pulmonology", 1200, "7654321098", "Lungs", "MD", "2023-03-01", 12),
        ("D4", "Dr. Sunita Reddy", "Oncology", 1500, "6543210987", "Cancer", "MD", "2023-04-01", 15),
        ("D5", "Dr. Vikram Patel", "General Medicine", 700, "5432109876", "General", "MD", "2023-05-01", 5)
    ]
    cursor.executemany('''
        INSERT INTO Doctor 
        (Doctor_ID, Name, Specialization, Fee, Contact, Department, Qualification, Date_of_Joining, Experience)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', doctors)

    # Add 10 Patients (Indian Names)
    patients = [
        ("P1", "Rahul Kumar", 35, "Male", "123 Gandhi Nagar, Delhi", "1111111111", "O+", "2222222222", "ABC Insurance", "Heart Disease", "D1"),
        ("P2", "Priya Singh", 28, "Female", "456 Nehru Road, Mumbai", "3333333333", "A+", "4444444444", "XYZ Insurance", "Diabetes", "D2"),
        ("P3", "Amit Patel", 45, "Male", "789 Tagore Lane, Bangalore", "5555555555", "B+", "6666666666", "DEF Insurance", "Asthma", "D3"),
        ("P4", "Anjali Desai", 60, "Female", "101 Shivaji Marg, Pune", "7777777777", "AB+", "8888888888", "GHI Insurance", "Cancer", "D4"),
        ("P5", "Ravi Verma", 50, "Male", "202 MG Road, Kolkata", "9999999999", "O-", "0000000000", "JKL Insurance", "Hypertension", "D5"),
        ("P6", "Kavita Joshi", 25, "Female", "303 Patel Chowk, Ahmedabad", "1212121212", "A-", "3434343434", "MNO Insurance", "Arthritis", "D1"),
        ("P7", "Sanjay Mehta", 70, "Male", "404 Gandhi Road, Chennai", "5656565656", "B-", "7878787878", "PQR Insurance", "Heart Disease", "D2"),
        ("P8", "Neha Kapoor", 40, "Female", "505 Nehru Street, Hyderabad", "9090909090", "AB-", "2323232323", "STU Insurance", "Diabetes", "D3"),
        ("P9", "Vijay Malhotra", 55, "Male", "606 Tagore Road, Jaipur", "4545454545", "O+", "6767676767", "VWX Insurance", "Asthma", "D4"),
        ("P10", "Sonia Choudhary", 30, "Female", "707 Shivaji Lane, Lucknow", "8989898989", "A+", "0101010101", "YZA Insurance", "Cancer", "D5")
    ]
    cursor.executemany('''
        INSERT INTO Patient 
        (Patient_ID, Name, Age, Gender, Address, Contact, Blood_Type, Emergency_Contact, Insurance_Details, Disease, Doctor_ID)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', patients)

    # Room Allocation (50% of patients hospitalized)
    room_allocations = [
        ("P1", 1, "2023-10-01", None),  # Still in hospital
        ("P2", 2, "2023-09-25", "2023-10-01"),  # Discharged
        ("P3", 3, "2023-10-05", None),  # Still in hospital
        ("P4", 4, "2023-09-20", "2023-09-30"),  # Discharged
        ("P5", 5, "2023-10-10", None),  # Still in hospital
    ]
    cursor.executemany('''
        INSERT INTO Room_Allocation 
        (Patient_ID, Room_Number, Admission_Date, Discharge_Date)
        VALUES (%s, %s, %s, %s)
    ''', room_allocations)

    # Billing (for discharged patients)
    bills = [
        ("P2", 500 * 6, 800, 500 * 6 + 800, "Paid"),  # 6 days in hospital
        ("P4", 500 * 10, 1500, 500 * 10 + 1500, "Pending")  # 10 days in hospital
    ]
    cursor.executemany('''
        INSERT INTO Billing 
        (Patient_ID, Room_Charges, Doctor_Fees, Total_Amount, Payment_Status)
        VALUES (%s, %s, %s, %s, %s)
    ''', bills)

    conn.commit()
    conn.close()
    print("✅ Sample Indian data added successfully!")
    
def view_unallocated_patients():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            p.Patient_ID, 
            p.Name, 
            p.Disease,
            p.Contact
        FROM Patient p
        WHERE p.Doctor_ID IS NULL
        ORDER BY CAST(SUBSTRING(p.Patient_ID, 2) AS UNSIGNED)
    ''')
    
    unallocated_patients = cursor.fetchall()
    
    if unallocated_patients:
        print("\n=== Unallocated Patients ===")
        print("ID | Name | Disease | Contact")
        print("-" * 50)
        for p in unallocated_patients:
            print(f"{p[0]} | {p[1]} | {p[2]} | {p[3]}")
    else:
        print("\nAll patients are allocated to doctors!")
    
    conn.close()
def view_current_patients():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            p.Patient_ID, p.Name, p.Age, p.Gender, p.Contact, 
            p.Blood_Type, p.Disease,
            d.Name AS Doctor_Name, d.Specialization AS Doctor_Specialization,
            ra.Room_Number, ra.Admission_Date
        FROM Patient p
        LEFT JOIN Doctor d ON p.Doctor_ID = d.Doctor_ID
        LEFT JOIN Room_Allocation ra ON p.Patient_ID = ra.Patient_ID
        WHERE ra.Discharge_Date IS NULL
        ORDER BY CAST(SUBSTRING(p.Patient_ID, 2) AS UNSIGNED)  -- Numerical sorting
    ''')
    # ... rest of the code ...
    
    current_patients = cursor.fetchall()
    
    if current_patients:
        print("\n=== Current Patients (In Hospital) ===")
        print("ID | Name | Age | Gender | Contact | Blood Type | Disease | Doctor | Specialization | Room | Admission Date")
        print("-" * 120)
        for p in current_patients:
            print(f"{p[0]} | {p[1]} | {p[2]} | {p[3]} | {p[4]} | {p[5]} | {p[6]} | {p[7] or 'Not Assigned'} | {p[8] or 'N/A'} | {p[9] or 'N/A'} | {p[10] or 'N/A'}")
    else:
        print("\nNo current patients found!")
    
    conn.close()

def view_discharged_patients():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            p.Patient_ID, p.Name, p.Age, p.Gender, p.Contact, 
            p.Blood_Type, p.Disease,
            d.Name AS Doctor_Name, d.Specialization AS Doctor_Specialization,
            ra.Room_Number, ra.Admission_Date, ra.Discharge_Date,
            b.Total_Amount, b.Payment_Status
        FROM Patient p
        LEFT JOIN Doctor d ON p.Doctor_ID = d.Doctor_ID
        LEFT JOIN Room_Allocation ra ON p.Patient_ID = ra.Patient_ID
        LEFT JOIN Billing b ON p.Patient_ID = b.Patient_ID
        WHERE ra.Discharge_Date IS NOT NULL
        ORDER BY CAST(SUBSTRING(p.Patient_ID, 2) AS UNSIGNED)  -- Numerical sorting
    ''')
    # ... rest of the code ...
    
    discharged_patients = cursor.fetchall()
    
    if discharged_patients:
        print("\n=== Discharged Patients ===")
        print("ID | Name | Age | Gender | Contact | Blood Type | Disease | Doctor | Specialization | Room | Admission Date | Discharge Date | Total Amount | Payment Status")
        print("-" * 150)
        for p in discharged_patients:
            print(f"{p[0]} | {p[1]} | {p[2]} | {p[3]} | {p[4]} | {p[5]} | {p[6]} | {p[7] or 'Not Assigned'} | {p[8] or 'N/A'} | {p[9] or 'N/A'} | {p[10] or 'N/A'} | {p[11] or 'N/A'} | ₹{p[12]} | {p[13]}")
    else:
        print("\nNo discharged patients found!")
    
    conn.close()
    

# ==================== ROOM ALLOCATION LOGIC ====================
def allocate_room_to_patient():
    conn = connect_db()
    cursor = conn.cursor()
    
    patient_id = input("Enter Patient ID to allocate room: ")
    
    # ========== NEW CODE: CHECK ACTIVE ALLOCATION ==========
    cursor.execute('''SELECT * FROM Room_Allocation 
                   WHERE Patient_ID = %s 
                   AND Discharge_Date IS NULL''', (patient_id,))
    if cursor.fetchone():
        print("\n❌ Error: Patient already has an active room allocation!")
        conn.close()
        return
    
    # Proceed with allocation if no active room
    # ... rest of your existing code ...

    
    # Check existing allocation
    cursor.execute('''SELECT * FROM Room_Allocation 
                   WHERE Patient_ID = %s AND Discharge_Date IS NULL''', (patient_id,))
    if cursor.fetchone():
        print("\nError: Patient already has active room allocation!")
        conn.close()
        return

    # Allocation mode selection
    print("\nChoose allocation mode:")
    print("1. Automatic Allocation")
    print("2. Manual Room Selection")
    mode = input("Enter choice (1/2): ")

    room_number = None
    
    if mode == '1':  # Automatic allocation
        # Find first available room (1-10) with space
        cursor.execute('''
            SELECT Room_Number FROM (
                SELECT Room_Number, COUNT(*) as occupants 
                FROM Room_Allocation 
                WHERE Discharge_Date IS NULL
                AND Room_Number BETWEEN 1 AND 10
                GROUP BY Room_Number
                HAVING occupants < 5
                ORDER BY Room_Number ASC
            ) AS available_rooms 
            UNION 
            SELECT t.Room_Number 
            FROM (
                SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 
                UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
            ) t(Room_Number)
            LEFT JOIN Room_Allocation ra 
            ON t.Room_Number = ra.Room_Number AND ra.Discharge_Date IS NULL
            WHERE ra.Room_Number IS NULL
            ORDER BY Room_Number ASC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        room_number = result[0] if result else None

    elif mode == '2':  # Manual selection
        while True:
            try:
                room_number = int(input("Enter room number (1-10): "))
                if not 1 <= room_number <= 10:
                    print("Invalid room! Must be between 1-10")
                    continue
                
                # Check room capacity
                cursor.execute('''
                    SELECT COUNT(*) FROM Room_Allocation 
                    WHERE Room_Number = %s 
                    AND Discharge_Date IS NULL
                ''', (room_number,))
                count = cursor.fetchone()[0]
                
                if count >= 5:
                    print(f"Room {room_number} is full (5/5 patients)")
                    continue
                    
                break  # Valid room selected
                
            except ValueError:
                print("Invalid input! Enter number between 1-10")

    # Final allocation
    if room_number:
        admission_date = datetime.now().date()
        cursor.execute('''INSERT INTO Room_Allocation 
                       (Room_Number, Patient_ID, Admission_Date)
                       VALUES (%s, %s, %s)''', 
                       (room_number, patient_id, admission_date))
        conn.commit()
        print(f"\nPatient {patient_id} allocated to Room {room_number}")
    else:
        print("\nError: No available rooms!")

    conn.close()



def remove_doctor():
    conn = connect_db()
    cursor = conn.cursor()
    
    doctor_id = input("Enter Doctor ID to remove: ")
    
    # Validate doctor exists
    cursor.execute('SELECT * FROM Doctor WHERE Doctor_ID = %s', (doctor_id,))
    if not cursor.fetchone():
        print("Error: Doctor does not exist!")
        conn.close()
        return
    
    confirm = input(f"Are you sure you want to remove Doctor {doctor_id}? (yes/no): ").lower()
    if confirm != 'yes':
        print("Deletion cancelled!")
        conn.close()
        return
    
    # Archive doctor
    cursor.execute('''
        INSERT INTO Removed_Doctors 
        SELECT *, CURDATE() FROM Doctor 
        WHERE Doctor_ID = %s
    ''', (doctor_id,))
    
    # Unassign patients
    cursor.execute('''
        UPDATE Patient 
        SET Doctor_ID = NULL 
        WHERE Doctor_ID = %s
    ''', (doctor_id,))
    
    # Delete doctor
    cursor.execute('DELETE FROM Doctor WHERE Doctor_ID = %s', (doctor_id,))
    
    conn.commit()
    print(f"Doctor {doctor_id} removed and patients unassigned!")
    conn.close()
    
    
    
def remove_patient():
    conn = connect_db()
    cursor = conn.cursor()
    
    patient_id = input("Enter Patient ID to remove: ")
    
    # Validate patient exists
    cursor.execute('SELECT * FROM Patient WHERE Patient_ID = %s', (patient_id,))
    if not cursor.fetchone():
        print("Error: Patient does not exist!")
        conn.close()
        return
    
    confirm = input(f"Are you sure you want to remove Patient {patient_id}? (yes/no): ").lower()
    if confirm != 'yes':
        print("Deletion cancelled!")
        conn.close()
        return
    
    # Archive patient
    cursor.execute('''
        INSERT INTO Removed_Patients 
        SELECT *, CURDATE() FROM Patient 
        WHERE Patient_ID = %s
    ''', (patient_id,))
    
    # Delete related records
    cursor.execute('DELETE FROM Billing WHERE Patient_ID = %s', (patient_id,))
    cursor.execute('DELETE FROM Room_Allocation WHERE Patient_ID = %s', (patient_id,))
    cursor.execute('DELETE FROM Patient WHERE Patient_ID = %s', (patient_id,))
    
    conn.commit()
    print(f"Patient {patient_id} removed successfully!")
    conn.close()
    
def change_patient_room():
    conn = connect_db()
    cursor = conn.cursor()
    
    patient_id = input("Enter Patient ID to change room: ")
    
    # Verify current allocation
    cursor.execute('''SELECT Room_Number FROM Room_Allocation 
                   WHERE Patient_ID = %s AND Discharge_Date IS NULL''', (patient_id,))
    current_room = cursor.fetchone()
    
    if not current_room:
        print("\nError: Patient has no active room allocation!")
        conn.close()
        return
    
    # Get new room number
    while True:
        try:
            new_room = int(input("Enter new room number (1-10): "))
            if not 1 <= new_room <= 10:
                print("Invalid room! Must be between 1-10")
                continue
                
            # Check new room capacity
            cursor.execute('''
                SELECT COUNT(*) FROM Room_Allocation 
                WHERE Room_Number = %s 
                AND Discharge_Date IS NULL
            ''', (new_room,))
            count = cursor.fetchone()[0]
            
            if count >= 5:
                print(f"Room {new_room} is full (5/5 patients)")
                continue
                
            break  # Valid room
                
        except ValueError:
            print("Invalid input! Enter number between 1-10")

    # Update allocation
    cursor.execute('''
        UPDATE Room_Allocation 
        SET Room_Number = %s 
        WHERE Patient_ID = %s 
        AND Discharge_Date IS NULL
    ''', (new_room, patient_id))
    
    conn.commit()
    print(f"\nPatient {patient_id} moved from Room {current_room[0]} to Room {new_room}")
    conn.close() 

# ==================== MAIN MENU SYSTEM ====================
def main():
    
    create_database()
    create_tables()

    while True:
        print("\n=== HOSPITAL MANAGEMENT SYSTEM ===")
        print("1. Patient Portal")
        print("2. Doctor Portal")
        print("3. Administrative Panel")
        print("4. Exit")

        
        choice = input("\nEnter your role: ")
        
        if choice == '1':
            while True:
                print("\nPATIENT PORTAL")
                print("1. Register New Patient")
                print("2. Get Patient ID")
                print("3. View Allocated Doctors")
                print("4. View Room Allocation")
                print("5. Request Discharge")
                print("6. Return to Main Menu")
                
                sub_choice = input("\nChoose option: ")
                
                if sub_choice == '1': register_patient()
                elif sub_choice == '2': get_patient_id()
                elif sub_choice == '3': view_patient_doctor()
                elif sub_choice == '4': view_patient_room()
                elif sub_choice == '5': patient_discharge()
                elif sub_choice == '6': break
                else: print("Invalid choice!")
        
        elif choice == '2':
            while True:
                print("\nDOCTOR PORTAL")
                print("1. Register New Doctor")
                print("2. Get Doctor ID")
                print("3. View My Patients")
                print("4. Return to Main Menu")
                
                sub_choice = input("\nChoose option: ")
                
                if sub_choice == '1': register_doctor()
                elif sub_choice == '2': get_doctor_id()
                elif sub_choice == '3': view_doctor_patients()
                elif sub_choice == '4': break
                else: print("Invalid choice!")
        
        elif choice == '3':
            while True:
                print("\nADMINISTRATIVE PANEL")
                print("1. View All Patients")
                print("2. View All Doctors")
                print("3. View Room Allocations")
                print("4. View Available Doctors")
                print("5. View Unallocated Patients")
                print("6. View Current Patients")
                print("7. View Discharged Patients")
                print("8. Remove a Patient")
                print("9. Remove a Doctor")
                print("10. Allocate Room to Patient")
                print("11. View Removed Patients")
                print("12. View Removed Doctors")
                print("13. Change Patient Room")
                print("14. Return to Main Menu")
            
                sub_choice = input("\nChoose option: ")
            
                if sub_choice == '1': view_all_patients()
                elif sub_choice == '2': view_all_doctors()
                elif sub_choice == '3': view_allocated_rooms()
                elif sub_choice == '4': view_available_doctors()
                elif sub_choice == '5': view_unallocated_patients()
                elif sub_choice == '6': view_current_patients()
                elif sub_choice == '7': view_discharged_patients()
                elif sub_choice == '8': remove_patient()
                elif sub_choice == '9': remove_doctor()
                elif sub_choice == '10': allocate_room_to_patient()
                elif sub_choice == '11': view_removed_patients()
                elif sub_choice == '12': view_removed_doctors()
                elif sub_choice == '13': change_patient_room()
                elif sub_choice == '14': break
                else: print("Invalid choice!")
                
        

        elif choice=='4':
            break
        else:
            print("Invalid choice")
if __name__ == "__main__":
    main()

