import numpy as np

from app.models.schemas import ChildChunk, ParentDocument


def _vector_from_seed(seed: int, dims: int = 1536) -> list[float]:
    rng = np.random.default_rng(seed)
    vector = rng.normal(0, 1, dims).astype(np.float32)
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector.tolist()


_PARENTS = [
    (
        "Hypertension management includes lifestyle change, medication titration, and monitoring for end-organ damage.",
        {"topic": "cardiology", "tags": ["hypertension", "medication"]},
    ),
    (
        "Type 2 diabetes care combines nutrition, physical activity, glucose-lowering drugs, and kidney risk monitoring.",
        {"topic": "endocrinology", "tags": ["diabetes", "metabolic"]},
    ),
    (
        "Asthma control relies on trigger avoidance, inhaled therapies, action plans, and periodic lung function testing.",
        {"topic": "pulmonology", "tags": ["asthma", "airway"]},
    ),
    (
        "Acute stroke pathways prioritize rapid imaging, reperfusion eligibility checks, and secondary prevention counseling.",
        {"topic": "neurology", "tags": ["stroke", "emergency"]},
    ),
    (
        "Osteoarthritis treatment emphasizes exercise, pain control, bracing, and escalation to procedures when needed.",
        {"topic": "orthopedics", "tags": ["osteoarthritis", "pain"]},
    ),
    (
        "Chronic kidney disease management includes blood pressure goals, proteinuria reduction, and renal dosing safety.",
        {"topic": "nephrology", "tags": ["ckd", "renal"]},
    ),
    (
        "Depression care requires screening, psychotherapy options, medication response tracking, and relapse prevention.",
        {"topic": "psychiatry", "tags": ["depression", "screening"]},
    ),
    (
        "Community-acquired pneumonia care covers risk stratification, empiric antibiotics, oxygen support, and follow-up.",
        {"topic": "infectious_disease", "tags": ["pneumonia", "antibiotics"]},
    ),
    (
        "Prenatal care addresses trimester screening, nutrition, blood pressure checks, and warning signs education.",
        {"topic": "obstetrics", "tags": ["prenatal", "maternal"]},
    ),
    (
        "Oncology supportive care balances symptom management, treatment toxicity surveillance, and palliative planning.",
        {"topic": "oncology", "tags": ["cancer", "supportive"]},
    ),
]


PARENT_STORE: list[ParentDocument] = [
    ParentDocument(parent_id=i + 1, text=text, metadata=metadata)
    for i, (text, metadata) in enumerate(_PARENTS)
]


_CHUNKS_BY_PARENT: dict[int, list[str]] = {
    1: [
        "Initial treatment for stage 1 hypertension often starts with sodium reduction and regular aerobic exercise.",
        "ACE inhibitors are common first-line options when patients have diabetes or chronic kidney disease.",
        "Home blood pressure logs can uncover white-coat effects and improve therapy adjustments.",
        "Persistent blood pressure above target requires dose escalation or combination therapy.",
        "Clinicians monitor retinal, cardiac, and renal complications to detect end-organ impact.",
    ],
    2: [
        "Metformin remains a common first-line medication when kidney function is adequate.",
        "Nutrition plans focus on glycemic control, weight reduction, and sustainable food patterns.",
        "A1c goals should be individualized by age, comorbidity burden, and hypoglycemia risk.",
        "SGLT2 inhibitors can lower renal and cardiovascular risk in selected patients.",
        "Routine urine albumin testing helps detect early diabetic kidney disease.",
    ],
    3: [
        "Controller inhalers reduce airway inflammation and prevent frequent exacerbations.",
        "Rescue inhalers should be used for acute bronchospasm and symptom spikes.",
        "Trigger control includes smoke avoidance, allergen reduction, and vaccination adherence.",
        "Written asthma action plans improve adherence and emergency preparedness.",
        "Spirometry trends help classify severity and adjust long-term treatment intensity.",
    ],
    4: [
        "Stroke protocols emphasize immediate neurologic assessment and symptom onset timing.",
        "Non-contrast CT is performed rapidly to distinguish ischemic and hemorrhagic events.",
        "Eligible ischemic stroke patients may receive thrombolysis within established windows.",
        "Mechanical thrombectomy evaluation depends on vessel occlusion and imaging criteria.",
        "Secondary prevention includes antiplatelet therapy, statins, and lifestyle risk reduction.",
    ],
    5: [
        "Exercise therapy strengthens periarticular muscles and improves joint stability.",
        "Topical NSAIDs provide pain control with lower systemic exposure for many patients.",
        "Weight loss can meaningfully reduce knee load and pain severity.",
        "Assistive devices such as canes can improve mobility and reduce fall risk.",
        "Joint replacement is considered when conservative options fail to maintain function.",
    ],
    6: [
        "Blood pressure control slows progression of chronic kidney disease in many etiologies.",
        "RAAS blockade can reduce proteinuria and protect renal function over time.",
        "Medication dosing should be adjusted to estimated glomerular filtration rate.",
        "Anemia and mineral bone disease are common complications in advanced CKD.",
        "Nephrology referral is recommended for rapid decline or complex electrolyte disorders.",
    ],
    7: [
        "Validated screening tools support early recognition of depressive symptoms.",
        "Cognitive behavioral therapy can reduce symptom burden and improve coping skills.",
        "SSRIs are frequently selected for first-line pharmacologic treatment.",
        "Response should be monitored over weeks with adjustment for tolerability.",
        "Relapse prevention includes maintenance therapy and structured follow-up planning.",
    ],
    8: [
        "Severity scores help determine outpatient treatment versus hospital admission.",
        "Empiric antibiotic selection considers local resistance and comorbidity profile.",
        "Oxygen therapy is provided when saturation falls below accepted targets.",
        "Hydration and airway clearance support recovery in moderate pneumonia cases.",
        "Follow-up imaging may be needed in persistent symptoms or high-risk patients.",
    ],
    9: [
        "First trimester visits include folate counseling and baseline laboratory screening.",
        "Blood pressure and urine checks help detect hypertensive disorders early.",
        "Gestational diabetes screening typically occurs in the second trimester.",
        "Vaccination review includes influenza and pertussis timing discussions.",
        "Patients are educated on warning signs such as bleeding or reduced fetal movement.",
    ],
    10: [
        "Antiemetics and nutrition support can reduce treatment-related symptom burden.",
        "Pain management plans should be individualized and reassessed frequently.",
        "Myelosuppression monitoring guides dose timing and infection precautions.",
        "Psychosocial support improves adherence and quality of life during therapy.",
        "Early palliative care integration can improve symptom control and goal alignment.",
    ],
}


CHILD_STORE: list[ChildChunk] = []
_child_id = 1
for parent_id, chunks in _CHUNKS_BY_PARENT.items():
    for chunk_index, text in enumerate(chunks):
        CHILD_STORE.append(
            ChildChunk(
                child_id=_child_id,
                parent_id=parent_id,
                chunk_index=chunk_index,
                text=text,
                vector=_vector_from_seed(seed=(parent_id * 10_000 + _child_id)),
            )
        )
        _child_id += 1


def get_parent_by_id(parent_id: int) -> ParentDocument | None:
    for parent in PARENT_STORE:
        if parent.parent_id == parent_id:
            return parent
    return None
