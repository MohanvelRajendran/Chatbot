-- Drop tables if they exist to start fresh
DROP TABLE IF EXISTS AdverseEvents;
DROP TABLE IF EXISTS Demography;

-- =================================================================
-- Demography Table
-- Stores clinical and demographic details for each patient.
-- =================================================================
CREATE TABLE Demography (
    patient_id INT PRIMARY KEY,
    study_id VARCHAR(50) NOT NULL,
    age INT,
    gender VARCHAR(10),
    race VARCHAR(50),
    country VARCHAR(50)
);

-- =================================================================
-- Adverse Events Table
-- Stores details about each adverse event.
--  It is linked to the Demography table via patient_id.
-- =================================================================
CREATE TABLE AdverseEvents (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT, -- SQLite-compatible auto-increment
    patient_id INT NOT NULL,
    event_term VARCHAR(255) NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('Mild', 'Moderate', 'Severe')),
    start_date DATE,
    outcome VARCHAR(100),
    FOREIGN KEY (patient_id) REFERENCES Demography(patient_id)
);

-- =================================================================
-- Sample Data Insertion
-- Let's add some data to make the tables useful.
-- =================================================================

-- Insert sample patients into the Demography table
INSERT INTO Demography (patient_id, study_id, age, gender, race, country) VALUES
(101, 'STUDY-ABC', 55, 'Female', 'Caucasian', 'USA'),
(102, 'STUDY-ABC', 62, 'Male', 'Asian', 'Japan'),
(103, 'STUDY-XYZ', 48, 'Male', 'Caucasian', 'USA'),
(104, 'STUDY-ABC', 71, 'Female', 'Black or African American', 'Canada'),
(105, 'STUDY-XYZ', 68, 'Male', 'Hispanic or Latino', 'Mexico'),
(106, 'STUDY-ABC', 59, 'Female', 'Caucasian', 'UK'),
(107, 'STUDY-XYZ', 75, 'Male', 'Asian', 'South Korea');

-- Insert sample adverse events
INSERT INTO AdverseEvents (patient_id, event_term, severity, start_date, outcome) VALUES
(101, 'Headache', 'Mild', '2023-04-12', 'Resolved'),
(101, 'Nausea', 'Moderate', '2023-04-13', 'Resolved'),
(102, 'Fatigue', 'Mild', '2023-05-01', 'Ongoing'),
(103, 'Dizziness', 'Severe', '2023-06-20', 'Resolved'),
(104, 'Headache', 'Moderate', '2023-07-15', 'Ongoing'),
(102, 'Joint Pain', 'Moderate', '2023-05-15', 'Ongoing'),
(105, 'High Blood Pressure', 'Severe', '2023-08-01', 'Ongoing'),
(106, 'Insomnia', 'Moderate', '2023-08-10', 'Resolved'),
(106, 'Anxiety', 'Mild', '2023-08-11', 'Ongoing');