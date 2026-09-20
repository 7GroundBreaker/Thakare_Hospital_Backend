import io
from datetime import date, time, timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from content.models import Article, ArticleCategory, GalleryCategory, GalleryImage, Testimonial
from hospital.models import Doctor, DoctorSchedule, Service, SiteSettings, Speciality

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = None

# Candidate bold/regular TrueType fonts to try before falling back to PIL's
# tiny built-in bitmap font. Missing files are silently skipped.
_FONT_CANDIDATES = {
    "bold": ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"],
    "regular": ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"],
}


def _load_font(size, bold=False):
    if Image is None:
        return None
    for path in _FONT_CANDIDATES["bold" if bold else "regular"]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _placeholder_image(label, size=(800, 600), bg=(9, 105, 92), fg=(255, 255, 255)):
    """Generates a plain, clearly-a-placeholder JPEG in memory so local dev
    has something visual to render instead of blank CmsImage tiles."""
    if Image is None:
        return None
    img = Image.new("RGB", size, color=bg)
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), label)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size[0] - w) / 2, (size[1] - h) / 2), label, fill=fg)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return ContentFile(buf.getvalue(), name=f"{slugify(label)[:80]}.jpg")


# Brand-matched gradient pairs (see frontend/src/app/globals.css tokens) that
# gallery placeholders cycle through so the grid reads as one coherent set
# instead of a repeated flat color.
_GALLERY_GRADIENTS = [
    ((10, 75, 69), (18, 118, 108)),   # primary-700 -> primary-500
    ((13, 96, 88), (63, 168, 133)),   # primary-600 -> secondary-500
    ((63, 168, 133), (10, 75, 69)),   # secondary-500 -> primary-700
    ((6, 46, 42), (13, 96, 88)),      # primary-900 -> primary-600
    ((198, 111, 48), (224, 138, 69)), # warm-600 -> warm-500 (used sparingly)
]


def _gallery_placeholder_image(label, index, size=(900, 600)):
    """Generates a branded gradient tile with soft decorative blobs and a
    bold caption — a clearly-a-placeholder image, but one that reads as an
    intentional design rather than a flat color swatch with tiny text."""
    if Image is None:
        return None

    w, h = size
    top, bottom = _GALLERY_GRADIENTS[index % len(_GALLERY_GRADIENTS)]

    img = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        row_color = tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3))
        draw.line([(0, y), (w, y)], fill=row_color)

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.ellipse([w * 0.55, -h * 0.3, w * 1.2, h * 0.55], fill=(255, 255, 255, 26))
    odraw.ellipse([-w * 0.25, h * 0.5, w * 0.3, h * 1.3], fill=(255, 255, 255, 18))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    accent_x, accent_y = int(w * 0.07), int(h * 0.78)
    draw.line([(accent_x, accent_y), (accent_x + 44, accent_y)], fill=(255, 255, 255), width=4)
    draw.text(
        (accent_x, accent_y + 12),
        label,
        font=_load_font(30, bold=True),
        fill=(255, 255, 255),
    )

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return ContentFile(buf.getvalue(), name=f"{slugify(label)[:80]}.jpg")


class Command(BaseCommand):
    """Fills in obviously-fake placeholder data (contact details, doctor
    bios, testimonials, articles, gallery images) purely so the frontend has
    something to render during local development/integration testing.

    This is NOT the same as `seed_data` — that command intentionally leaves
    real-world facts (fees, hours, phone numbers, testimonials) blank until
    the hospital confirms them. This command is dev-only scaffolding and
    should never be run against a production database.
    """

    help = "Seed obviously-fake placeholder content for local frontend/backend integration testing."

    def handle(self, *args, **options):
        self.seed_site_settings()
        self.seed_doctor_details()
        self.seed_speciality_media()
        self.seed_testimonials()
        self.seed_articles()
        self.seed_gallery()
        self.stdout.write(self.style.SUCCESS("Dummy content ready for local development."))

    def seed_site_settings(self):
        s = SiteSettings.load()
        if not s.phone:
            s.phone = "+91 98765 43210"
        if not s.whatsapp_number:
            s.whatsapp_number = "+91 98765 43210"
        if not s.email:
            s.email = "info@thakarehospital.example"
        if not s.address:
            s.address = "123 MG Road, Nashik, Maharashtra 422001, India"
        if not s.opening_hours:
            s.opening_hours = "Mon-Sat: 9:00 AM - 8:00 PM\nSun: 9:00 AM - 1:00 PM (Emergency only)"
        if not s.google_maps_url:
            s.google_maps_url = "https://maps.google.com/?q=Thakare+Hospital+Nashik"
        if s.latitude is None:
            s.latitude = 19.997454
        if s.longitude is None:
            s.longitude = 73.789803
        if not s.tagline:
            s.tagline = "Compassionate care, trusted expertise."
        if not s.footer_description:
            s.footer_description = (
                "Thakare Hospital provides pediatric, gynaecology & obstetrics, and "
                "dental care to families across the region."
            )
        if not s.facebook_url:
            s.facebook_url = "https://facebook.com/thakarehospital"
        if not s.instagram_url:
            s.instagram_url = "https://instagram.com/thakarehospital"
        if not s.google_review_url:
            s.google_review_url = "https://g.page/r/thakarehospital/review"
        if not s.emergency_phone:
            s.emergency_phone = "+91 98765 00000"
            s.emergency_enabled = True
            s.emergency_availability = "24x7"
            s.emergency_message = "For medical emergencies, call us directly or visit the hospital immediately."
        if not s.privacy_policy:
            s.privacy_policy = (
                "This is placeholder privacy policy text for local development. "
                "Thakare Hospital respects your privacy and only collects the information "
                "needed to schedule and manage your appointments. Replace this text with "
                "the hospital's reviewed privacy policy before going live."
            )
        if not s.terms_and_conditions:
            s.terms_and_conditions = (
                "This is placeholder terms & conditions text for local development. "
                "By booking an appointment through this website, you agree to be contacted "
                "by Thakare Hospital staff regarding your request. Replace this text with "
                "the hospital's reviewed terms before going live."
            )
        s.save()
        self.stdout.write("Site settings: dummy contact details filled in.")

    def seed_doctor_details(self):
        details = {
            "dr-indranil-thakare": {
                "qualification": "MBBS, MD (Pediatrics)",
                "experience": "12+ years",
                "consultation_fee": "Rs. 500",
                "clinic_location": "Thakare Hospital, Ground Floor, OPD 1",
                "phone": "+91 98765 43211",
                "whatsapp": "+91 98765 43211",
                "sub_speciality": "Neonatal & Child Care",
                "languages": "English, Hindi, Marathi",
                "areas_of_expertise": (
                    "Newborn care\nVaccination\nGrowth & nutrition counselling\n"
                    "Common childhood illnesses"
                ),
                "consultation_timings_note": "Mon-Sat, 10:00 AM - 1:00 PM & 5:00 PM - 8:00 PM",
            },
            "dr-anjali-indranil-thakare": {
                "qualification": "MBBS, MS (Obstetrics & Gynaecology)",
                "experience": "10+ years",
                "consultation_fee": "Rs. 600",
                "clinic_location": "Thakare Hospital, First Floor, OPD 2",
                "phone": "+91 98765 43212",
                "whatsapp": "+91 98765 43212",
                "sub_speciality": "High-risk Pregnancy Care",
                "languages": "English, Hindi, Marathi",
                "areas_of_expertise": (
                    "Antenatal & postnatal care\nNormal & assisted deliveries\n"
                    "Routine gynaecological checkups\nFamily planning counselling"
                ),
                "consultation_timings_note": "Mon-Sat, 11:00 AM - 2:00 PM & 6:00 PM - 8:30 PM",
            },
            "dr-kaustubh-thakare": {
                "qualification": "BDS, MDS (Oral & Maxillofacial Surgery)",
                "experience": "8+ years",
                "consultation_fee": "Rs. 400",
                "clinic_location": "Thakare Hospital, Ground Floor, Dental Wing",
                "phone": "+91 98765 43213",
                "whatsapp": "+91 98765 43213",
                "sub_speciality": "Cosmetic & Restorative Dentistry",
                "languages": "English, Hindi, Marathi",
                "areas_of_expertise": (
                    "Routine dental checkups\nScaling & polishing\nFillings & root canal\n"
                    "Tooth extraction"
                ),
                "consultation_timings_note": "Mon-Sat, 10:00 AM - 1:00 PM & 4:00 PM - 7:00 PM",
            },
            "dr-ketki-kaustubh-thakare": {
                "experience": "5+ years",
                "consultation_fee": "Rs. 400",
                "clinic_location": "Thakare Hospital, Ground Floor, Dental Wing",
                "phone": "+91 98765 43214",
                "whatsapp": "+91 98765 43214",
                "sub_speciality": "Preventive & Family Dentistry",
                "languages": "English, Hindi, Marathi",
                "areas_of_expertise": (
                    "Routine dental checkups\nPreventive care & oral hygiene\nFillings\n"
                    "Pediatric dental care"
                ),
                "consultation_timings_note": "Mon-Sat, 10:00 AM - 1:00 PM & 4:00 PM - 7:00 PM",
            },
        }
        for slug, fields in details.items():
            doctor = Doctor.objects.filter(slug=slug).first()
            if not doctor:
                continue
            changed = False
            for field, value in fields.items():
                if not getattr(doctor, field):
                    setattr(doctor, field, value)
                    changed = True
            if not doctor.profile_photo:
                img = _placeholder_image(doctor.full_name, bg=(9, 105, 92))
                if img:
                    doctor.profile_photo.save(img.name, img, save=False)
                    changed = True
            if changed:
                doctor.save()
            if not doctor.schedules.exists():
                for day in range(0, 6):  # Monday(0) - Saturday(5)
                    DoctorSchedule.objects.create(
                        doctor=doctor, day_of_week=day, start_time=time(10, 0), end_time=time(13, 0),
                        slot_duration_minutes=20,
                    )
                    DoctorSchedule.objects.create(
                        doctor=doctor, day_of_week=day, start_time=time(17, 0), end_time=time(20, 0),
                        slot_duration_minutes=20,
                    )
            self.stdout.write(f"Doctor details filled: {doctor.full_name}")

    def seed_speciality_media(self):
        content = {
            "pediatrics": (
                "Our pediatrics team supports your child's health from birth through "
                "adolescence, with a focus on preventive care, timely vaccination and "
                "guidance for parents at every stage of growth.",
                "Consult us for routine check-ups, vaccination schedules, growth "
                "concerns, fever, infections, or any question about your child's health.",
            ),
            "gynaecology-obstetrics": (
                "We offer complete women's health services, from routine gynaecological "
                "care to antenatal and postnatal support through every stage of pregnancy.",
                "Consult us for pregnancy care, routine gynaecological checkups, "
                "menstrual health concerns, or family planning guidance.",
            ),
            "dental-care": (
                "Our dental team provides preventive and restorative care in a "
                "comfortable, modern setting for the whole family.",
                "Consult us for routine checkups, cleaning, cavities, tooth pain, or "
                "any concern about your oral health.",
            ),
        }
        for slug, (description, when) in content.items():
            spec = Speciality.objects.filter(slug=slug).first()
            if not spec:
                continue
            changed = False
            if not spec.description:
                spec.description = description
                changed = True
            if not spec.when_to_consult:
                spec.when_to_consult = when
                changed = True
            if not spec.hero_image:
                img = _placeholder_image(f"{spec.name} - Hero", size=(1200, 500), bg=(14, 116, 144))
                if img:
                    spec.hero_image.save(img.name, img, save=False)
                    changed = True
            if not spec.card_image:
                img = _placeholder_image(spec.name, size=(600, 400), bg=(14, 116, 144))
                if img:
                    spec.card_image.save(img.name, img, save=False)
                    changed = True
            if changed:
                spec.save()
            self.stdout.write(f"Speciality media/content filled: {spec.name}")

    def seed_testimonials(self):
        if Testimonial.objects.exists():
            self.stdout.write("Testimonials already present, skipping.")
            return
        data = [
            ("Priya Sharma", "pediatrics", "dr-indranil-thakare", 5,
             "Dr. Thakare is wonderful with children. My son looks forward to his checkups now!"),
            ("Rahul Deshmukh", "pediatrics", "dr-indranil-thakare", 5,
             "Very patient and thorough. Explained everything clearly and put us at ease."),
            ("Sneha Patil", "gynaecology-obstetrics", "dr-anjali-indranil-thakare", 5,
             "Dr. Anjali guided me through my entire pregnancy with so much care and attention."),
            ("Meera Kulkarni", "gynaecology-obstetrics", "dr-anjali-indranil-thakare", 4,
             "Professional, warm, and always available to answer my questions."),
            ("Amit Joshi", "dental-care", "dr-kaustubh-thakare", 5,
             "Painless treatment and a very clean, modern clinic. Highly recommend!"),
            ("Kavita Singh", "dental-care", "dr-kaustubh-thakare", 5,
             "Great experience from start to finish. The staff is friendly and efficient."),
        ]
        today = date.today()
        for index, (name, spec_slug, doc_slug, rating, text) in enumerate(data):
            Testimonial.objects.create(
                patient_name=name,
                testimonial_text=text,
                speciality=Speciality.objects.filter(slug=spec_slug).first(),
                doctor=Doctor.objects.filter(slug=doc_slug).first(),
                rating=rating,
                date=today - timedelta(days=index * 9),
                consent_confirmed=True,
                is_published=True,
                display_order=index,
            )
        self.stdout.write("Dummy testimonials created.")

    def seed_articles(self):
        if Article.objects.exists():
            self.stdout.write("Articles already present, skipping.")
            return
        data = [
            ("Vaccination Schedule for Infants: A Parent's Guide", "Pediatrics", "pediatrics",
             "A quick overview of the recommended vaccination timeline for your baby's first two years.",
             "Vaccinations protect your child from serious diseases. This guide walks through the "
             "standard immunization schedule recommended for infants and toddlers, what to expect at "
             "each visit, and tips for a smoother experience for both parent and child.",
             "Follow the recommended schedule\nKeep a vaccination record\nMild fever after a shot is "
             "normal\nConsult your pediatrician about missed doses",
             "vaccination, infants, pediatrics"),
            ("Managing Fever in Young Children", "Pediatrics", "pediatrics",
             "Practical, safe steps parents can take when a child develops a fever.",
             "Fever is one of the most common reasons parents bring children to the pediatrician. "
             "Learn how to monitor your child's temperature, when home care is appropriate, and the "
             "warning signs that mean it's time to see a doctor.",
             "Track the temperature and symptoms\nOffer fluids and rest\nUse fever medication as "
             "advised\nSeek care for high or persistent fever",
             "fever, child health, pediatrics"),
            ("What to Expect During Your First Antenatal Visit", "Pregnancy", "gynaecology-obstetrics",
             "An overview of the tests and discussions that typically happen at your first prenatal "
             "appointment.",
             "Your first antenatal visit sets the foundation for a healthy pregnancy. This article "
             "explains the routine checks, screenings, and lifestyle guidance you can expect, so you "
             "can walk in prepared and informed.",
             "Confirm your due date\nDiscuss your medical history\nRoutine blood and urine tests\n"
             "Plan your antenatal visit schedule",
             "pregnancy, antenatal care, women's health"),
            ("Women's Wellness: Routine Health Checkups That Matter", "Women's Health",
             "gynaecology-obstetrics",
             "Why regular gynaecological checkups are an important part of preventive care.",
             "Routine checkups help catch potential health concerns early. Here's a look at the "
             "screenings and conversations that should be part of a woman's regular healthcare "
             "routine at every life stage.",
             "Annual checkups support early detection\nDiscuss any changes with your doctor\n"
             "Preventive care reduces long-term risk",
             "women's health, wellness, checkup"),
            ("Everyday Habits for Healthy Teeth and Gums", "Dental Health", "dental-care",
             "Simple daily habits that go a long way in keeping your smile healthy.",
             "Good oral hygiene is about consistency. This article covers brushing and flossing "
             "technique, diet tips, and how often you should visit the dentist for a routine checkup.",
             "Brush twice daily with fluoride toothpaste\nFloss once a day\nLimit sugary snacks and "
             "drinks\nVisit the dentist every six months",
             "dental care, oral hygiene, prevention"),
            ("When Should You See a Dentist for Tooth Pain?", "Dental Health", "dental-care",
             "Understanding the difference between minor sensitivity and a dental emergency.",
             "Tooth pain can range from mild sensitivity to a sign of a serious problem. Learn what "
             "symptoms warrant a same-day visit and how to manage discomfort until you're seen.",
             "Persistent pain needs prompt attention\nSwelling can indicate infection\nAvoid very "
             "hot or cold foods until seen\nOver-the-counter pain relief is a temporary measure",
             "dental care, tooth pain, emergency"),
        ]
        today = date.today()
        for index, (title, cat_name, spec_slug, short_desc, content, takeaways, tags) in enumerate(data):
            article = Article.objects.create(
                title=title,
                category=ArticleCategory.objects.filter(name=cat_name).first(),
                speciality=Speciality.objects.filter(slug=spec_slug).first(),
                author="Thakare Hospital Team",
                publish_date=today - timedelta(days=index * 5),
                short_description=short_desc,
                content=content,
                key_takeaways=takeaways,
                tags=tags,
                is_published=True,
            )
            img = _placeholder_image(title, size=(1000, 600), bg=(217, 119, 6))
            if img:
                article.featured_image.save(img.name, img, save=True)
        self.stdout.write("Dummy Health Library articles created.")

    def seed_gallery(self):
        # Regenerate every time this is run so a re-run of the dummy-data
        # command picks up improvements to the placeholder artwork below,
        # rather than silently keeping older, lower-quality images.
        GalleryImage.objects.all().delete()

        plan = [
            ("Hospital", "Hospital Reception"),
            ("Hospital", "Hospital Exterior"),
            ("Doctors", "Our Doctors"),
            ("Facilities", "OPD Waiting Area"),
            ("Facilities", "Consultation Room"),
            ("Pediatrics", "Pediatric Ward"),
            ("Maternity", "Maternity Ward"),
            ("Dental", "Dental Treatment Room"),
            ("Events", "Health Awareness Camp"),
            ("Community", "Community Outreach"),
            ("Clinic", "Clinic Corridor"),
            ("Other", "Hospital Signage"),
        ]
        for index, (cat_name, caption) in enumerate(plan):
            img = _gallery_placeholder_image(caption, index)
            if not img:
                continue
            gallery_image = GalleryImage(
                category=GalleryCategory.objects.filter(name=cat_name).first(),
                caption=caption,
                is_featured=index < 3,
                display_order=index,
            )
            gallery_image.image.save(img.name, img, save=True)
        self.stdout.write(f"Gallery refreshed with {len(plan)} placeholder images across all categories.")
