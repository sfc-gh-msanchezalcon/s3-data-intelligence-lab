import boto3
import json
import os
import struct
import wave
import io

s3 = boto3.client('s3', region_name='eu-central-1')
bucket_name = 'snowflake-s3-intelligence-lab-msanchez'

# --- PDF SAMPLES (simple text-based PDFs) ---
pdf_documents = [
    {
        "filename": "lab_report_smith_2024.pdf",
        "content": """Patient: John Smith, DOB: 1965-03-15
Provider: Dr. Sarah Johnson, MD - Internal Medicine
Date: 2024-11-15

LABORATORY RESULTS
Complete Blood Count (CBC):
- WBC: 7.2 x10^3/uL (Normal: 4.5-11.0)
- RBC: 4.8 x10^6/uL (Normal: 4.7-6.1)
- Hemoglobin: 14.2 g/dL (Normal: 13.5-17.5)
- Hematocrit: 42% (Normal: 38.3-48.6)
- Platelets: 245 x10^3/uL (Normal: 150-400)

Metabolic Panel:
- Glucose: 142 mg/dL (HIGH - Normal: 70-100)
- HbA1c: 7.1% (HIGH - Normal: <5.7%)
- Creatinine: 1.1 mg/dL (Normal: 0.7-1.3)
- BUN: 18 mg/dL (Normal: 7-20)

Assessment: Type 2 Diabetes Mellitus, suboptimal glycemic control.
Plan: Increase Metformin to 1000mg BID. Recheck HbA1c in 3 months.
Referral to endocrinology if no improvement."""
    },
    {
        "filename": "discharge_summary_jones_2024.pdf",
        "content": """DISCHARGE SUMMARY
Patient: Maria Jones, DOB: 1978-08-22
MRN: 4456789
Admission Date: 2024-10-01
Discharge Date: 2024-10-05
Attending: Dr. Michael Chen, MD - Cardiology

Primary Diagnosis: Acute Myocardial Infarction (STEMI)
Secondary Diagnoses: Hypertension, Hyperlipidemia

Hospital Course:
Patient presented to ED with crushing chest pain radiating to left arm.
ECG showed ST elevation in leads II, III, aVF. Troponin elevated at 4.2 ng/mL.
Emergent cardiac catheterization revealed 95% occlusion of RCA.
Successful PCI with drug-eluting stent placement.
Post-procedure course uncomplicated. Echo showed EF 45%.

Medications at Discharge:
1. Aspirin 81mg daily
2. Clopidogrel 75mg daily (12 months)
3. Atorvastatin 80mg daily
4. Metoprolol 50mg BID
5. Lisinopril 10mg daily

Follow-up: Cardiology clinic in 2 weeks. Cardiac rehabilitation referral."""
    },
    {
        "filename": "prescription_williams_2024.pdf",
        "content": """PRESCRIPTION
Date: 2024-11-20
Provider: Dr. Emily Rodriguez, MD
DEA#: FR1234567
NPI: 1234567890

Patient: Robert Williams, DOB: 1955-12-03
Address: 456 Oak Street, Springfield, IL 62701

Rx 1: Lisinopril 20mg tablets
Sig: Take one tablet by mouth daily
Qty: 30 (thirty)
Refills: 5

Rx 2: Amlodipine 5mg tablets
Sig: Take one tablet by mouth daily
Qty: 30 (thirty)
Refills: 5

Rx 3: Metformin 500mg tablets
Sig: Take one tablet by mouth twice daily with meals
Qty: 60 (sixty)
Refills: 5

Diagnosis: Essential hypertension (I10), Type 2 diabetes (E11.9)
Next appointment: 3 months"""
    },
    {
        "filename": "radiology_report_garcia_2024.pdf",
        "content": """RADIOLOGY REPORT
Patient: Ana Garcia, DOB: 1990-04-18
MRN: 7789012
Exam Date: 2024-11-10
Exam: CT Chest with contrast
Ordering Provider: Dr. James Wilson, MD - Pulmonology
Radiologist: Dr. Patricia Lee, MD

CLINICAL HISTORY: Persistent cough x 3 weeks, hemoptysis

TECHNIQUE: Helical CT of the chest performed with IV contrast.

FINDINGS:
- Lungs: 2.3cm spiculated nodule in right upper lobe (segment 1).
  No additional pulmonary nodules identified.
- Mediastinum: No lymphadenopathy. Heart size normal.
- Pleura: No effusion. No pneumothorax.
- Bones: No suspicious osseous lesions.

IMPRESSION:
1. Solitary spiculated pulmonary nodule in right upper lobe measuring 2.3cm.
   Findings are suspicious for malignancy. PET/CT recommended.
2. Otherwise unremarkable chest CT.

RECOMMENDATION: PET/CT for further evaluation. Pulmonology consultation."""
    },
    {
        "filename": "progress_note_patel_2024.pdf",
        "content": """PROGRESS NOTE
Patient: Raj Patel, DOB: 1970-07-25
Date: 2024-11-18
Provider: Dr. Lisa Thompson, MD - Psychiatry

Chief Complaint: Follow-up for Major Depressive Disorder

Subjective:
Patient reports moderate improvement in mood since starting Sertraline 100mg
3 weeks ago. Sleep improved from 4 hours to 6 hours nightly. Appetite
returning. Denies suicidal ideation. Still experiencing difficulty concentrating
at work. Reports mild nausea in the mornings.

Objective:
- Appearance: Well-groomed, appropriate dress
- Behavior: Good eye contact, cooperative
- Mood: "Better but not great"
- Affect: Congruent, mildly restricted range
- Thought process: Linear, goal-directed
- PHQ-9 score: 12 (was 19 at last visit)

Assessment: MDD, single episode, moderate - responding to treatment
Plan:
1. Continue Sertraline 100mg daily
2. Add Melatonin 3mg at bedtime for residual insomnia
3. Cognitive Behavioral Therapy referral
4. Follow-up in 4 weeks
5. Return sooner if symptoms worsen"""
    },
    {
        "filename": "surgical_report_brown_2024.pdf",
        "content": """OPERATIVE REPORT
Patient: David Brown, DOB: 1960-01-30
MRN: 3345678
Date of Surgery: 2024-11-12
Surgeon: Dr. Robert Kim, MD - Orthopedic Surgery
Assistant: Dr. Amy Foster, MD

Procedure: Right Total Knee Arthroplasty

Preoperative Diagnosis: Severe osteoarthritis, right knee (M17.11)
Postoperative Diagnosis: Same

Anesthesia: Spinal with sedation

Operative Findings:
Severe tricompartmental osteoarthritis with complete loss of cartilage
in medial and lateral compartments. Large osteophytes present.
ACL absent. PCL intact but attenuated.

Procedure Details:
Standard medial parapatellar approach. Distal femoral cut performed
with 5 degrees of valgus. Tibial cut with 3 degrees posterior slope.
Cemented posterior-stabilized implant (Size: Femur 5, Tibia 4, Insert 10mm).
Patellar resurfacing performed.
Excellent stability and range of motion (0-120 degrees) after trial components.

EBL: 150mL
Complications: None
Disposition: Recovery room in stable condition"""
    }
]

# --- TXT SAMPLES (clinical notes, nursing observations) ---
txt_documents = [
    {
        "filename": "nursing_notes_icu_2024.txt",
        "content": """ICU NURSING NOTES - Night Shift
Patient: Maria Jones, Room 4B-12
Date: 2024-10-02, 23:00 - 07:00
Nurse: RN Jennifer Adams

2300: Patient resting comfortably. VS: BP 128/78, HR 72, RR 16, SpO2 98% on 2L NC.
      Cardiac monitor showing NSR. Groin site intact, no bleeding/hematoma.
      Pain 2/10, medicated with Tylenol 650mg PO.

0100: Repositioned. Voided 300mL clear yellow urine. IV Heparin drip at 18 units/kg/hr.
      PTT due at 0600.

0300: BP dropped to 98/62. Patient diaphoretic. Called rapid response.
      MD at bedside within 5 minutes. 500mL NS bolus administered.
      BP improved to 112/70 within 20 minutes. HR 88. No chest pain.
      ECG obtained - no new ST changes. Troponin drawn.

0500: Stable post-intervention. BP 118/72, HR 76. Patient sleeping.
      PTT result: 68 seconds (therapeutic range 60-100).

0700: Morning assessment. Patient awake, alert, oriented x4.
      Breakfast tray delivered. Ambulated to bathroom with assistance.
      Groin site: small ecchymosis noted, no hematoma. Pedal pulses 2+ bilateral.
      Handoff to day shift RN completed."""
    },
    {
        "filename": "referral_letter_endocrinology.txt",
        "content": """REFERRAL LETTER
From: Dr. Sarah Johnson, MD - Internal Medicine
To: Dr. Amanda Pierce, MD - Endocrinology
Date: 2024-11-16
Re: John Smith, DOB: 1965-03-15

Dear Dr. Pierce,

I am referring Mr. Smith for evaluation and management of his Type 2 Diabetes
Mellitus with suboptimal glycemic control despite medication adjustments.

Current medications:
- Metformin 1000mg BID (recently increased from 500mg BID)
- Lisinopril 10mg daily (for associated hypertension)
- Atorvastatin 20mg daily

Recent labs (2024-11-15):
- HbA1c: 7.1% (target <7.0%, was 6.8% 6 months ago)
- Fasting glucose: 142 mg/dL
- Lipid panel: TC 198, LDL 118, HDL 42, TG 190

Complications screening:
- Retinal exam (2024-08): No diabetic retinopathy
- Monofilament test: Normal sensation bilateral feet
- Urine microalbumin: 45 mg/g creatinine (mildly elevated)

The patient is motivated but struggling with dietary compliance.
BMI 32.4. Would appreciate your recommendations regarding additional
pharmacotherapy (GLP-1 agonist?) and insulin initiation threshold.

Thank you for your expertise.
Sincerely,
Dr. Sarah Johnson"""
    },
    {
        "filename": "therapy_session_notes.txt",
        "content": """THERAPY SESSION NOTES
Therapist: Dr. Karen Mitchell, PhD - Clinical Psychology
Patient: Raj Patel
Session #: 4 (of planned 12-session CBT course)
Date: 2024-11-20
Duration: 50 minutes

Session Focus: Cognitive restructuring - identifying automatic negative thoughts

Key Discussion Points:
- Patient identified 3 recurring negative thought patterns this week:
  1. "I'm failing at everything" (all-or-nothing thinking)
  2. "Everyone at work thinks I'm incompetent" (mind reading)
  3. "Things will never get better" (fortune telling/catastrophizing)

- Used thought records to challenge each belief with evidence
- Patient was able to generate alternative balanced thoughts
- Discussed behavioral activation: patient agreed to resume daily walks
  and one social activity per week

Mood Rating (0-10): Start of session: 4, End of session: 6
PHQ-9 administered: Score 10 (down from 12 two weeks ago)

Homework Assigned:
1. Complete daily thought records (at least one per day)
2. Walk 20 minutes x 5 days
3. Schedule one social activity
4. Continue mindfulness meditation app (10 min daily)

Clinical Notes:
Patient showing steady improvement. Engagement in therapy is good.
Medication adjustment (Sertraline 100mg) appears to be helping.
Will continue CBT protocol as planned. No safety concerns."""
    },
    {
        "filename": "patient_intake_form_martinez.txt",
        "content": """PATIENT INTAKE FORM
Date: 2024-11-01
Facility: Springfield Medical Center

DEMOGRAPHICS:
Name: Carlos Martinez
DOB: 1982-11-14
Gender: Male
Address: 789 Elm Drive, Springfield, IL 62702
Phone: (217) 555-0142
Emergency Contact: Sofia Martinez (wife) - (217) 555-0143
Insurance: Blue Cross Blue Shield PPO, ID# BCB882114

CHIEF COMPLAINT: Chronic lower back pain x 6 months

MEDICAL HISTORY:
- Lumbar disc herniation (L4-L5) diagnosed 2023
- Hypertension - controlled on medication
- Appendectomy (2005)
- No known drug allergies (NKDA)

CURRENT MEDICATIONS:
1. Losartan 50mg daily
2. Ibuprofen 600mg TID (as needed for pain)
3. Cyclobenzaprine 10mg at bedtime

SOCIAL HISTORY:
- Occupation: Construction worker
- Tobacco: Former smoker (quit 2019, 10 pack-year history)
- Alcohol: Social (2-3 beers/week)
- Exercise: Limited due to back pain
- Lives with wife and 2 children (ages 8, 12)

REVIEW OF SYSTEMS:
- Constitutional: No fever, weight stable
- Musculoskeletal: LBP radiating to left leg, worse with bending/lifting
- Neurological: Occasional numbness left foot, no weakness
- Psychiatric: Mild frustration/irritability related to pain and work limitations

GOALS OF CARE: Return to full work duties, reduce pain to manageable level"""
    }
]

# --- AUDIO SAMPLES (WAV files with silence - will be "transcribed" by AI) ---
# We create minimal valid WAV files. AI_TRANSCRIBE needs real audio,
# so we'll generate simple tone WAV files with some structure.

def generate_wav_bytes(duration_seconds=5, sample_rate=16000, frequency=440):
    """Generate a simple WAV file with a tone."""
    import math
    num_samples = int(duration_seconds * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # Generate a simple tone that varies (simulating speech-like patterns)
        amplitude = int(16000 * math.sin(2 * math.pi * frequency * t) *
                       (0.5 + 0.5 * math.sin(2 * math.pi * 2 * t)))
        samples.append(struct.pack('<h', max(-32768, min(32767, amplitude))))

    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(samples))
    return buf.getvalue()

audio_files = [
    {"filename": "consultation_cardiology_jones.wav", "duration": 8},
    {"filename": "consultation_diabetes_smith.wav", "duration": 6},
    {"filename": "consultation_orthopedic_brown.wav", "duration": 7},
    {"filename": "consultation_psychiatry_patel.wav", "duration": 5},
    {"filename": "consultation_pulmonology_garcia.wav", "duration": 6},
]

def create_simple_pdf(text_content):
    """Create a minimal valid PDF from text."""
    lines = text_content.strip().split('\n')
    stream_content = ""
    y = 750
    for line in lines:
        escaped = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        stream_content += f"BT /F1 10 Tf 50 {y} Td ({escaped}) Tj ET\n"
        y -= 14
        if y < 50:
            break

    stream_bytes = stream_content.encode('latin-1')
    stream_length = len(stream_bytes)

    pdf = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length {stream_length}>>
stream
{stream_content}endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Courier>>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
trailer<</Size 6/Root 1 0 R>>
startxref
0
%%EOF"""
    return pdf.encode('latin-1')


# Upload PDFs
print("Uploading PDF files...")
for doc in pdf_documents:
    pdf_bytes = create_simple_pdf(doc["content"])
    s3.put_object(
        Bucket=bucket_name,
        Key=f"healthcare/pdfs/{doc['filename']}",
        Body=pdf_bytes,
        ContentType='application/pdf'
    )
    print(f"  Uploaded: {doc['filename']} ({len(pdf_bytes)} bytes)")

# Upload TXT files
print("\nUploading TXT files...")
for doc in txt_documents:
    s3.put_object(
        Bucket=bucket_name,
        Key=f"healthcare/txt/{doc['filename']}",
        Body=doc["content"].encode('utf-8'),
        ContentType='text/plain'
    )
    print(f"  Uploaded: {doc['filename']} ({len(doc['content'])} bytes)")

# Upload Audio files
print("\nUploading Audio files...")
for audio in audio_files:
    wav_bytes = generate_wav_bytes(duration_seconds=audio["duration"])
    s3.put_object(
        Bucket=bucket_name,
        Key=f"healthcare/audio/{audio['filename']}",
        Body=wav_bytes,
        ContentType='audio/wav'
    )
    print(f"  Uploaded: {audio['filename']} ({len(wav_bytes)} bytes)")

print(f"\nDone! Uploaded {len(pdf_documents)} PDFs, {len(txt_documents)} TXTs, {len(audio_files)} audio files")
