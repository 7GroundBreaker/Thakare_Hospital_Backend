from django.core.management.base import BaseCommand

from content.models import ArticleCategory, FAQ, FAQCategory, GalleryCategory
from hospital.models import ConditionTreated, Doctor, Service, SiteSettings, Speciality


class Command(BaseCommand):
    """Seed the three named doctors, their specialities and structural
    (non-medical-claim) content categories.

    Per the hospital brief, this command deliberately does NOT invent:
    degrees, years of experience, awards, certifications, consultation
    fees, timings, phone numbers, email addresses, the hospital address,
    or any treatment/outcome claims. Those fields are left blank and are
    marked as TODO placeholders for the hospital administrator to fill in
    through the Django admin.
    """

    help = "Seed initial specialities, doctors and structural content categories."

    def handle(self, *args, **options):
        self.seed_site_settings()
        specialities = self.seed_specialities()
        self.seed_doctors(specialities)
        self.seed_article_categories()
        self.seed_gallery_categories()
        self.seed_faqs()
        self.stdout.write(self.style.SUCCESS("Seed data created successfully."))

    def seed_site_settings(self):
        settings_obj = SiteSettings.load()
        if not settings_obj.hospital_name:
            settings_obj.hospital_name = "Thakare Hospital"
        settings_obj.whatsapp_message_template = (
            settings_obj.whatsapp_message_template
            or "Hello Thakare Hospital, I would like to book an appointment."
        )
        settings_obj.medical_disclaimer = settings_obj.medical_disclaimer or (
            "Information provided on this website is for general educational "
            "purposes and should not be considered a substitute for professional "
            "medical advice."
        )
        settings_obj.save()
        self.stdout.write("Site settings ready (fill in phone/address/maps in the admin).")

    def seed_specialities(self):
        data = [
            {
                "name": "Pediatrics",
                "slug": "pediatrics",
                "short_description": "Compassionate healthcare for infants, children and adolescents.",
                "icon": "baby",
                "conditions": [
                    "Newborn care",
                    "Infant care",
                    "Child health",
                    "Adolescent health",
                    "Growth monitoring",
                    "Nutrition guidance",
                    "Vaccination guidance",
                    "Fever",
                    "Cough and cold",
                    "Respiratory problems",
                    "Digestive problems",
                    "General pediatric consultation",
                ],
            },
            {
                "name": "Gynaecology & Obstetrics",
                "slug": "gynaecology-obstetrics",
                "short_description": "Comprehensive care for women's health, pregnancy and maternity needs.",
                "icon": "heart-pulse",
                "conditions": [
                    "Women's health",
                    "Pregnancy care",
                    "Antenatal care",
                    "Postnatal care",
                    "Routine gynaecological consultation",
                    "Women's wellness",
                    "Menstrual health",
                    "Reproductive health",
                ],
            },
            {
                "name": "Dental Care",
                "slug": "dental-care",
                "short_description": "Professional dental care focused on healthy smiles and comfortable treatment.",
                "icon": "tooth",
                "conditions": [
                    "Preventive dental care",
                    "Dental consultation",
                    "Oral hygiene",
                    "Dental examination",
                    "General dental care",
                ],
            },
        ]

        created = {}
        for index, item in enumerate(data):
            speciality, _ = Speciality.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "short_description": item["short_description"],
                    "icon": item["icon"],
                    "display_order": index,
                    "is_active": True,
                },
            )
            for cond_index, condition_name in enumerate(item["conditions"]):
                ConditionTreated.objects.update_or_create(
                    speciality=speciality,
                    name=condition_name,
                    defaults={"display_order": cond_index},
                )
            Service.objects.update_or_create(
                speciality=speciality,
                slug="general-consultation",
                defaults={
                    "name": "General Consultation",
                    "description": "Book a consultation with our specialist.",
                    "display_order": 0,
                    "is_active": True,
                },
            )
            created[item["slug"]] = speciality
            self.stdout.write(f"Speciality ready: {speciality.name}")
        return created

    def seed_doctors(self, specialities):
        doctors = [
            {
                "full_name": "Dr. Indranil Thakare",
                "slug": "dr-indranil-thakare",
                "designation": "Pediatrician",
                "speciality_slug": "pediatrics",
                "biography": "Compassionate healthcare for infants, children and adolescents.",
            },
            {
                "full_name": "Dr. Anjali Indranil Thakare",
                "slug": "dr-anjali-indranil-thakare",
                "designation": "Gynaecologist & Obstetrician",
                "speciality_slug": "gynaecology-obstetrics",
                "biography": "Comprehensive care for women's health, pregnancy and maternity needs.",
            },
            {
                "full_name": "Dr. Kaustubh Thakare",
                "slug": "dr-kaustubh-thakare",
                "designation": "Dental Surgeon",
                "speciality_slug": "dental-care",
                "biography": "Professional dental care focused on healthy smiles and comfortable treatment.",
            },
            {
                "full_name": "Dr. Ketki Kaustubh Thakare",
                "slug": "dr-ketki-kaustubh-thakare",
                "designation": "Dentist",
                # Confirmed by the hospital — unlike the other TODO fields below,
                # this is real, provided data, not an invented claim.
                "qualification": "BDS",
                "speciality_slug": "dental-care",
                "biography": "Professional dental care focused on healthy smiles and comfortable treatment.",
            },
        ]

        for index, item in enumerate(doctors):
            doctor, _ = Doctor.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "full_name": item["full_name"],
                    "designation": item["designation"],
                    "biography": item["biography"],
                    "display_order": index,
                    "is_active": True,
                    "booking_enabled": True,
                    "qualification": item.get("qualification", ""),
                    # Intentionally left blank — see command docstring.
                    "experience": "",
                    "consultation_fee": "",
                    "clinic_location": "",
                    "phone": "",
                    "whatsapp": "",
                },
            )
            doctor.specialities.set([specialities[item["speciality_slug"]]])
            self.stdout.write(f"Doctor ready: {doctor.full_name}")

    def seed_article_categories(self):
        names = [
            "Pediatrics",
            "Women's Health",
            "Pregnancy",
            "Dental Health",
            "General Health",
            "Preventive Care",
        ]
        for index, name in enumerate(names):
            ArticleCategory.objects.update_or_create(
                name=name, defaults={"display_order": index}
            )
        self.stdout.write("Health Library categories ready.")

    def seed_gallery_categories(self):
        names = [
            "Hospital",
            "Doctors",
            "Facilities",
            "Events",
            "Community",
            "Clinic",
            "Dental",
            "Pediatrics",
            "Maternity",
            "Other",
        ]
        for index, name in enumerate(names):
            GalleryCategory.objects.update_or_create(
                name=name, defaults={"display_order": index}
            )
        self.stdout.write("Gallery categories ready.")

    def seed_faqs(self):
        faqs = [
            {
                "question": "How do I book an appointment at Thakare Hospital?",
                "answer": (
                    "You can book an appointment online using the Book Appointment "
                    "form, call the hospital directly, or message us on WhatsApp."
                ),
                "category": FAQCategory.APPOINTMENTS,
            },
            {
                "question": "What should I bring to my first appointment?",
                "answer": (
                    "Please bring a valid ID and any previous medical records or "
                    "reports relevant to your visit."
                ),
                "category": FAQCategory.APPOINTMENTS,
            },
            {
                "question": "Can I reschedule or cancel my appointment?",
                "answer": (
                    "Yes. Contact the hospital by phone or WhatsApp and our team "
                    "will help you reschedule or cancel your appointment."
                ),
                "category": FAQCategory.APPOINTMENTS,
            },
        ]
        for index, item in enumerate(faqs):
            FAQ.objects.update_or_create(
                question=item["question"],
                defaults={
                    "answer": item["answer"],
                    "category": item["category"],
                    "display_order": index,
                    "is_published": True,
                },
            )
        self.stdout.write("Starter FAQs ready.")
