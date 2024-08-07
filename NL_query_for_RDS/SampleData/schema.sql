-- public.patient_admissions definition

-- Drop table

-- DROP TABLE public.patient_admissions;

CREATE TABLE public.patient_admissions (
	admission_number int4 NOT NULL,
	date_of_admission varchar(50) NULL,
	date_of_discharge varchar(50) NULL,
	age int4 NULL,
	gender varchar(50) NULL,
	rural varchar(50) NULL,
	type_of_admission_emergency_or_opd varchar(50) NULL,
	month_year varchar(50) NULL,
	duration_of_stay int4 NULL,
	duration_of_intensive_unit_stay int4 NULL,
	outcome varchar(50) NULL
);

-- public.patient_habits definition

-- Drop table

-- DROP TABLE public.patient_habits;

CREATE TABLE public.patient_habits (
	admission_number int4 NOT NULL,
	smoking int4 NULL,
	alcohol int4 NULL
);

-- public.diagnosis_report definition

-- Drop table

-- DROP TABLE public.diagnosis_report;

CREATE TABLE public.diagnosis_report (
	admission_number int4 NOT NULL,
	diabetes_mellitus int4 NULL,
	hypertension int4 NULL,
	coronary_artery_disease int4 NULL,
	cardiomyopathy int4 NULL,
	chronic_kidney_disease int4 NULL,
	haemoglobin float4 NULL,
	total_leukocytes_count float4 NULL,
	platelets varchar(50) NULL,
	glucose varchar(50) NULL,
	urea int4 NULL,
	creatinine float4 NULL,
	b_type_natriuretic_peptide varchar(50) NULL,
	raised_cardiac_enzymes int4 NULL,
	anaemia int4 NULL,
	heart_failure int4 NULL,
	pulmonary_embolism int4 NULL,
	chest_infection int4 NULL
);


-- public.mortality definition

-- Drop table

-- DROP TABLE public.mortality;

CREATE TABLE public.mortality (
	admission_number varchar(50) NOT NULL,
	age int4 NULL,
	gender varchar(50) NULL,
	rural_or_urban varchar(50) NULL,
	date_of_brought_dead varchar(50) NULL
);