-- Drop tables if they exist to start fresh
-- Order is important due to foreign key constraints.
DROP TABLE IF EXISTS vs;
DROP TABLE IF EXISTS ae;
DROP TABLE IF EXISTS dm;

-- =================================================================
-- Demography Table
-- Stores demographic details for each patient. This is the central patient table.
-- =================================================================
CREATE TABLE dm (
    patient_id INT PRIMARY KEY,
    study_id VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE,
    age INT, -- Age can be derived from DOB, but often stored for quick access
    gender VARCHAR(10),
    race VARCHAR(50),
    country VARCHAR(50)
);

-- =================================================================
-- Adverse Events Table
-- Stores details about each adverse event, linked to a patient.
-- =================================================================
CREATE TABLE ae (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT, -- SQLite-compatible auto-increment
    patient_id INT NOT NULL,
    event_term VARCHAR(255) NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('Mild', 'Moderate', 'Severe')),
    start_date DATE,
    outcome VARCHAR(100),
    FOREIGN KEY (patient_id) REFERENCES dm(patient_id) ON DELETE CASCADE
);

-- =================================================================
-- Vitals Table
-- Stores clinical vital signs for patients, linked to a patient.
-- =================================================================
CREATE TABLE vs (
    vitals_id INTEGER PRIMARY KEY AUTOINCREMENT, -- SQLite-compatible auto-increment
    patient_id INT NOT NULL,
    measurement_datetime DATETIME NOT NULL,
    heart_rate INT, -- beats per minute
    systolic_bp INT, -- mmHg
    diastolic_bp INT, -- mmHg
    body_temperature DECIMAL(4, 1), -- Celsius
    respiratory_rate INT, -- breaths per minute
    oxygen_saturation INT, -- SpO2 percentage
    FOREIGN KEY (patient_id) REFERENCES dm(patient_id) ON DELETE CASCADE
);

-- =================================================================
-- Sample Data Insertion
-- Let's add some data to make the tables useful.
-- =================================================================

-- Insert sample patients into the Demography table
INSERT INTO dm (patient_id, study_id, first_name, last_name, date_of_birth, age, gender, race, country) VALUES
(101, 'STUDY-ABC', 'Alice', 'Williams', '1968-03-15', 55, 'Female', 'Caucasian', 'USA'),
(102, 'STUDY-ABC', 'Kenji', 'Tanaka', '1961-07-22', 62, 'Male', 'Asian', 'Japan'),
(103, 'STUDY-XYZ', 'Robert', 'Miller', '1975-01-30', 48, 'Male', 'Caucasian', 'USA'),
(104, 'STUDY-ABC', 'Maria', 'Garcia', '1952-11-05', 71, 'Female', 'Black or African American', 'Canada'),
(105, 'STUDY-XYZ', 'Carlos', 'Rodriguez', '1955-09-12', 68, 'Male', 'Hispanic or Latino', 'Mexico'),
(106, 'STUDY-ABC', 'Emily', 'Brown', '1964-06-25', 59, 'Female', 'Caucasian', 'UK'),
(107, 'STUDY-XYZ', 'Jin-Ho', 'Park', '1948-02-18', 75, 'Male', 'Asian', 'South Korea');

-- Insert sample adverse events
INSERT INTO ae (patient_id, event_term, severity, start_date, outcome) VALUES
(101, 'Headache', 'Mild', '2023-04-12', 'Resolved'),
(101, 'Nausea', 'Moderate', '2023-04-13', 'Resolved'),
(102, 'Fatigue', 'Mild', '2023-05-01', 'Ongoing'),
(103, 'Dizziness', 'Severe', '2023-06-20', 'Resolved'),
(104, 'Headache', 'Moderate', '2023-07-15', 'Ongoing'),
(102, 'Joint Pain', 'Moderate', '2023-05-15', 'Ongoing'),
(105, 'High Blood Pressure', 'Severe', '2023-08-01', 'Ongoing'),
(106, 'Insomnia', 'Moderate', '2023-08-10', 'Resolved'),
(106, 'Anxiety', 'Mild', '2023-08-11', 'Ongoing');

-- Insert sample vitals data for the patients in the Demography table.
INSERT INTO vs (patient_id, measurement_datetime, heart_rate, systolic_bp, diastolic_bp, body_temperature, respiratory_rate, oxygen_saturation) VALUES
(101, '2023-04-12 09:00:00', 78, 125, 82, 36.8, 18, 98),
(101, '2023-04-13 09:05:00', 85, 128, 85, 37.2, 20, 97),
(102, '2023-05-01 10:15:00', 68, 118, 78, 36.5, 16, 99),
(104, '2023-07-15 11:00:00', 90, 140, 90, 37.5, 22, 96),
(104, '2023-07-16 11:30:00', 88, 138, 88, 37.3, 20, 97);