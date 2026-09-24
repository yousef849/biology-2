from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-key"
DATABASE = Path(__file__).parent / "database.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            grade INTEGER NOT NULL,
            points INTEGER DEFAULT 0
        )
    """)
    for username, password, grade in [
        ("student9", "password9", 9),
        ("student11", "password11", 11),
        ("student12", "password12", 12),
    ]:
        existing = cursor.execute(
            "SELECT id FROM students WHERE username = ?", (username,)
        ).fetchone()
        if existing is None:
            cursor.execute(
                "INSERT INTO students (username, password, grade, points) VALUES (?, ?, ?, ?)",
                (username, generate_password_hash(password), grade, 0),
            )
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    teacher_exists = cursor.execute(
        "SELECT id FROM teachers WHERE username = ?", ("teacherOmarQasim",)
    ).fetchone()
    if teacher_exists is None:
        cursor.execute(
            "INSERT INTO teachers (username, password) VALUES (?, ?)",
            ("teacherOmarQasim", generate_password_hash("123456789")),
        )
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            section_id TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            UNIQUE(student_id, section_id),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solved_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            UNIQUE(student_id, question_id),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            points INTEGER NOT NULL DEFAULT 10,
            UNIQUE(student_id, question_id),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS section_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            section_id TEXT NOT NULL,
            rating TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, section_id),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            attempt_number INTEGER NOT NULL,
            selected_index INTEGER NOT NULL,
            correct INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, question_id, attempt_number),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)
    connection.commit()
    connection.close()


# These questions use the current draft lesson content. Verify them against
# the textbook pages before treating them as an official textbook assessment.
LESSON_SECTIONS = [
    {
        "id": "section2",
        "number": 2,
        "title": "التفاعلات الكيميائية",
        "english": "Chemical Reactions",
        "summary": "التفاعلات الكيميائية تحوّل المواد المتفاعلة إلى نواتج جديدة من خلال تكسير روابط كيميائية وتكوين روابط أخرى.",
        "points": [
            "المتفاعلات هي المواد التي تبدأ التفاعل.",
            "النواتج هي المواد التي تتكوّن بعد التفاعل.",
            "من دلائل التفاعل: إنتاج حرارة أو ضوء، تكوّن غاز، أو تكوّن مادة صلبة جديدة.",
            "طاقة التنشيط هي الطاقة اللازمة لبدء التفاعل الكيميائي.",
            "الإنزيمات محفزات حيوية تساعد على تسريع التفاعلات داخل الكائنات الحية.",
        ],
        "hint": "ابحث عن الفرق بين المواد الموجودة قبل التفاعل والمواد المتكوّنة بعده.",
    },
    {
        "id": "section3",
        "number": 3,
        "title": "الماء والمحاليل",
        "english": "Water and Solutions",
        "summary": "تساعد قطبية الماء والروابط الهيدروجينية على تفسير كثير من خصائص الماء وأهميته للكائنات الحية.",
        "points": [
            "الماء جزيء قطبي لأن توزيع الإلكترونات فيه غير متساوٍ.",
            "تتكوّن الروابط الهيدروجينية بين جزيئات الماء.",
            "المحلول خليط متجانس يتكوّن من مذيب ومذاب.",
            "المذيب هو المادة التي تذيب المذاب، والمذاب هو المادة التي تذوب فيه.",
            "يقيس الرقم الهيدروجيني pH مدى حموضة المحلول أو قاعديته.",
        ],
        "hint": "تذكّر أن المذيب يذيب، والمذاب يذوب، وأن pH يرتبط بالحموضة والقاعدية.",
    },
    {
        "id": "section4",
        "number": 4,
        "title": "العناصر الأساسية اللازمة للحياة",
        "english": "Elements Essential for Life",
        "summary": "يُعد الكربون مكوّناً أساسياً في معظم الجزيئات الحيوية، ويمكنه تكوين روابط تساهمية متنوعة.",
        "points": [
            "يدخل الكربون في تركيب معظم الجزيئات الحيوية.",
            "يمكن لذرة الكربون تكوين أربع روابط تساهمية.",
            "الجزيئات الضخمة جزيئات كبيرة تتكوّن من وحدات أصغر.",
            "من الجزيئات الضخمة الحيوية: الكربوهيدرات والدهون والبروتينات والأحماض النووية.",
            "الكربوهيدرات قد تُستخدم كمصدر للطاقة أو للدعم الهيكلي، مثل السليلوز في النباتات.",
        ],
        "hint": "ركّز على عدد الروابط التي يكوّنها الكربون وعلى المجموعات الأربع للجزيئات الضخمة.",
    },
]

QUESTIONS = [{'id': 1, 'section_id': 'section2', 'text': 'ما المقصود بالمتفاعلات؟', 'options': ['المواد التي تبدأ التفاعل', 'المواد التي تتكوّن بعد التفاعل', 'الضوء الناتج', 'الماء فقط'], 'answer': 0, 'hint': 'فكّر في المواد الموجودة قبل بدء التفاعل.'}, {'id': 2, 'section_id': 'section2', 'text': 'ما المقصود بالنواتج؟', 'options': ['المواد التي تبدأ التفاعل', 'المواد التي تتكوّن بعد التفاعل', 'طاقة التنشيط فقط', 'الأدوات المستخدمة'], 'answer': 1, 'hint': 'النواتج تظهر بعد حدوث التفاعل.'}, {'id': 3, 'section_id': 'section2', 'text': 'أي علامة قد تدل على حدوث تفاعل كيميائي؟', 'options': ['زيادة عدد الغرف', 'تغيّر مكان الجسم فقط', 'تكوّن غاز أو إنتاج حرارة', 'تغيير اسم الوعاء'], 'answer': 2, 'hint': 'ابحث عن علامة تدل على تكوّن مادة أو طاقة جديدة.'}, {'id': 4, 'section_id': 'section2', 'text': 'ما طاقة التنشيط؟', 'options': ['الطاقة الموجودة في الطعام فقط', 'الطاقة التي توقف الضوء', 'الطاقة التي تلغي النواتج', 'الطاقة اللازمة لبدء التفاعل'], 'answer': 3, 'hint': 'هي حاجز طاقة يجب تجاوزه حتى يبدأ التفاعل.'}, {'id': 5, 'section_id': 'section2', 'text': 'ما وظيفة الإنزيمات؟', 'options': ['تسريع التفاعلات الحيوية', 'تحويل كل المواد إلى غاز', 'منع تكوّن الروابط', 'إيقاف كل التفاعلات'], 'answer': 0, 'hint': 'الإنزيمات محفزات حيوية.'}, {'id': 6, 'section_id': 'section2', 'text': 'أثناء التفاعل الكيميائي، ماذا يحدث للروابط؟', 'options': ['لا يحدث أي تغيير', 'تتكسر روابط وتتكوّن روابط أخرى', 'تختفي الذرات', 'يتحول كل شيء إلى ضوء'], 'answer': 1, 'hint': 'التفاعل يعيد ترتيب الذرات.'}, {'id': 7, 'section_id': 'section2', 'text': 'أي عبارة تميّز المتفاعلات عن النواتج؟', 'options': ['لا علاقة لهما بالتفاعل', 'كلاهما يعني الشيء نفسه', 'المتفاعلات تدخل والنواتج تتكوّن', 'النواتج تدخل والمتفاعلات تتكوّن'], 'answer': 2, 'hint': 'رتّب المصطلحين قبل التفاعل وبعده.'}, {'id': 8, 'section_id': 'section2', 'text': 'ما الذي يحدث للذرات في التفاعل الكيميائي؟', 'options': ['تتحول إلى ضوء دائماً', 'لا تشارك في التفاعل', 'تختفي تماماً', 'يعاد ترتيبها في مواد جديدة'], 'answer': 3, 'hint': 'الذرات تُعاد ترتيباتها ولا تختفي.'}, {'id': 9, 'section_id': 'section2', 'text': 'أي مما يلي مثال على تغير كيميائي؟', 'options': ['احتراق الخشب', 'تقطيع الورق', 'تغيير مكان كتاب', 'ذوبان الثلج'], 'answer': 0, 'hint': 'التغير الكيميائي ينتج مواد جديدة.'}, {'id': 10, 'section_id': 'section2', 'text': 'ما دور المحفز في التفاعل؟', 'options': ['يزيد طاقة التنشيط دائماً', 'يساعد التفاعل على الحدوث بسرعة أكبر', 'يمنع تكوّن النواتج', 'يحوّل الذرات إلى ضوء'], 'answer': 1, 'hint': 'المحفز يسهّل حدوث التفاعل.'}, {'id': 11, 'section_id': 'section2', 'text': 'أي خيار ليس دليلاً مباشراً على تفاعل كيميائي؟', 'options': ['تغيّر اللون بسبب مادة جديدة', 'تكوّن راسب', 'تحريك جسم من مكان إلى آخر', 'تكوّن فقاعات غاز'], 'answer': 2, 'hint': 'الحركة وحدها لا تعني تكوّن مادة جديدة.'}, {'id': 12, 'section_id': 'section2', 'text': 'ما المادة التي تكون موجودة في بداية التفاعل؟', 'options': ['الراسب فقط', 'المحفز فقط', 'الناتج', 'المتفاعل'], 'answer': 3, 'hint': 'المتفاعل يبدأ العملية الكيميائية.'}, {'id': 13, 'section_id': 'section2', 'text': 'ما المادة التي تتكوّن في نهاية التفاعل؟', 'options': ['الناتج', 'المذيب دائماً', 'المتفاعل فقط', 'طاقة التنشيط'], 'answer': 0, 'hint': 'الناتج هو ما يتكوّن بعد التفاعل.'}, {'id': 14, 'section_id': 'section2', 'text': 'لماذا تحتاج بعض التفاعلات إلى طاقة تنشيط؟', 'options': ['لتحويل الماء إلى ضوء', 'لبدء كسر بعض الروابط', 'لإزالة جميع الذرات', 'لمنع التصادمات'], 'answer': 1, 'hint': 'بدء التفاعل يتطلب تجاوز حاجز طاقة.'}, {'id': 15, 'section_id': 'section2', 'text': 'كيف تؤثر الإنزيمات عادةً في التفاعلات الحيوية؟', 'options': ['تمنع ارتباط الجزيئات', 'تبطئها دائماً', 'تسرّعها دون أن تُستهلك كلياً', 'تلغي النواتج'], 'answer': 2, 'hint': 'الإنزيم يعمل كمحفز حيوي.'}, {'id': 16, 'section_id': 'section2', 'text': 'ما المقصود بالتفاعل الكيميائي؟', 'options': ['تغير في الموقع فقط', 'تغير في الحجم دون أي مادة جديدة', 'تغير في الاسم فقط', 'تغير ينتج مواد جديدة'], 'answer': 3, 'hint': 'فكّر في تكوّن مواد بخصائص جديدة.'}, {'id': 17, 'section_id': 'section2', 'text': 'أي عبارة صحيحة عن النواتج؟', 'options': ['تتكوّن نتيجة التفاعل', 'لا تحتوي على ذرات', 'هي طاقة فقط', 'توجد قبل المتفاعلات'], 'answer': 0, 'hint': 'النواتج هي المواد الناتجة عن العملية.'}, {'id': 18, 'section_id': 'section2', 'text': 'عند ظهور راسب في محلول، ماذا قد يشير ذلك؟', 'options': ['تحول المحلول إلى ضوء', 'حدوث تفاعل كيميائي', 'اختفاء كل المواد', 'عدم حدوث أي تغير'], 'answer': 1, 'hint': 'الراسب مادة صلبة جديدة قد تتكوّن أثناء التفاعل.'}, {'id': 19, 'section_id': 'section2', 'text': 'ما العلاقة بين طاقة التنشيط وسرعة التفاعل؟', 'options': ['تلغي كل المحفزات', 'تمنع التصادمات دائماً', 'تجاوزها يسمح ببدء التفاعل', 'ليس لها علاقة ببدء التفاعل'], 'answer': 2, 'hint': 'يجب تجاوز حاجز طاقة التنشيط لبدء التفاعل.'}, {'id': 20, 'section_id': 'section2', 'text': 'أي جملة تلخّص دور الإنزيم؟', 'options': ['مادة توقف جميع العمليات', 'مادة تتحول دائماً إلى ناتج', 'مادة تمنع تكوّن الروابط', 'مادة تساعد على تسريع تفاعل حيوي'], 'answer': 3, 'hint': 'الإنزيمات تساعد التفاعلات الحيوية على الحدوث بسرعة أكبر.'}, {'id': 21, 'section_id': 'section3', 'text': 'ما مكوّنا المحلول؟', 'options': ['مذيب ومذاب', 'غاز وضوء', 'حمض وحرارة', 'ذرة وإلكترون'], 'answer': 0, 'hint': 'أحد المكوّنين يذيب والآخر يذوب.'}, {'id': 22, 'section_id': 'section3', 'text': 'لماذا يُعد الماء جزيئاً قطبياً؟', 'options': ['لأنه لا يكوّن روابط', 'لأن توزيع الإلكترونات غير متساوٍ', 'لأنه لا يحتوي على ذرات', 'لأنه صلب دائماً'], 'answer': 1, 'hint': 'القطبية تتعلق بتوزيع الشحنة.'}, {'id': 23, 'section_id': 'section3', 'text': 'بين ماذا تتكوّن الروابط الهيدروجينية في هذا الدرس؟', 'options': ['بين الضوء والحرارة', 'بين جميع المعادن فقط', 'بين جزيئات الماء', 'بين الأوعية فقط'], 'answer': 2, 'hint': 'فكّر في التجاذب بين جزيئات الماء.'}, {'id': 24, 'section_id': 'section3', 'text': 'ما وظيفة المذيب؟', 'options': ['المادة التي لا تختلط أبداً', 'المادة التي تنتج الضوء', 'المادة التي توقف الذوبان', 'المادة التي تذيب المذاب'], 'answer': 3, 'hint': 'اسم المذيب مرتبط بالفعل يذيب.'}, {'id': 25, 'section_id': 'section3', 'text': 'ما المقصود بالمذاب؟', 'options': ['المادة التي تذوب في المذيب', 'الوعاء المستخدم', 'الغاز الناتج من التفاعل', 'المادة التي تذيب غيرها'], 'answer': 0, 'hint': 'المذاب هو الجزء الذي يتم إذابته.'}, {'id': 26, 'section_id': 'section3', 'text': 'ماذا يقيس الرقم الهيدروجيني pH؟', 'options': ['كتلة المحلول', 'حموضة المحلول أو قاعديته', 'عدد الذرات فقط', 'درجة لمعان السائل'], 'answer': 1, 'hint': 'يرتبط pH بالحموضة والقاعدية.'}, {'id': 27, 'section_id': 'section3', 'text': 'أي وصف يناسب المحلول؟', 'options': ['غاز نقي دائماً', 'مادة صلبة فقط', 'خليط متجانس', 'مادة لا تحتوي على أي جسيمات'], 'answer': 2, 'hint': 'في المحلول تتوزع مكوّناته بصورة متجانسة.'}, {'id': 28, 'section_id': 'section3', 'text': 'عند إذابة الملح في الماء، ما المذيب؟', 'options': ['الهواء', 'البلورات فقط', 'الملح', 'الماء'], 'answer': 3, 'hint': 'المذيب هو المادة التي تذيب غيرها.'}, {'id': 29, 'section_id': 'section3', 'text': 'عند إذابة السكر في الماء، ما المذاب؟', 'options': ['السكر', 'الوعاء', 'الحرارة', 'الماء'], 'answer': 0, 'hint': 'المذاب هو المادة التي تذوب.'}, {'id': 30, 'section_id': 'section3', 'text': 'ما سبب قدرة الماء على إذابة مواد كثيرة؟', 'options': ['عدم تكوّن روابط فيه', 'قطبيته', 'عدم احتوائه على ذرات', 'كونه ضوءاً'], 'answer': 1, 'hint': 'قطبية الماء تساعده على التفاعل مع مواد مختلفة.'}, {'id': 31, 'section_id': 'section3', 'text': 'ما الذي يربط جزيئات الماء ببعضها؟', 'options': ['أشعة ضوئية', 'ذرات كربون فقط', 'روابط هيدروجينية', 'روابط معدنية فقط'], 'answer': 2, 'hint': 'توجد قوى تجاذب هيدروجينية بين جزيئات الماء.'}, {'id': 32, 'section_id': 'section3', 'text': 'أي محلول يُعد متجانساً؟', 'options': ['رمل وحصى منفصلان', 'زيت وقطع صلبة واضحة', 'صندوق من مواد مختلفة', 'ماء وملح مذاب بالتساوي'], 'answer': 3, 'hint': 'الخليط المتجانس يبدو موحداً في أجزائه.'}, {'id': 33, 'section_id': 'section3', 'text': 'إذا كان pH منخفضاً جداً، فالمحلول غالباً؟', 'options': ['حمضي', 'قاعدي جداً', 'ماء نقي دائماً', 'غازي فقط'], 'answer': 0, 'hint': 'القيم المنخفضة من pH ترتبط بالحموضة.'}, {'id': 34, 'section_id': 'section3', 'text': 'إذا كان pH مرتفعاً، فالمحلول غالباً؟', 'options': ['مكوّن من ضوء', 'قاعدي', 'حمضي دائماً', 'لا يحتوي على ماء'], 'answer': 1, 'hint': 'القيم المرتفعة من pH ترتبط بالقاعدية.'}, {'id': 35, 'section_id': 'section3', 'text': 'ما المقصود بقطبية الجزيء؟', 'options': ['عدم وجود روابط', 'تحول الجزيء إلى صلب دائماً', 'توزيع غير متساوٍ للشحنة', 'اختفاء الإلكترونات'], 'answer': 2, 'hint': 'القطبية تنتج عن عدم تساوي توزيع الشحنة.'}, {'id': 36, 'section_id': 'section3', 'text': 'أي عبارة عن الماء صحيحة؟', 'options': ['لا يتفاعل مع أي مادة', 'لا يمتلك قطبية', 'يتكوّن من ذرة واحدة فقط', 'جزيئاته يمكن أن تكوّن روابط هيدروجينية'], 'answer': 3, 'hint': 'جزيئات الماء تتجاذب بروابط هيدروجينية.'}, {'id': 37, 'section_id': 'section3', 'text': 'ما الذي يحدث للمذاب في المحلول؟', 'options': ['ينتشر داخل المذيب', 'يبقى دائماً منفصلاً فوقه', 'يتحول إلى ضوء', 'يختفي دون وجوده'], 'answer': 0, 'hint': 'المذاب يتوزع داخل المذيب.'}, {'id': 38, 'section_id': 'section3', 'text': 'أي مثال يمثل مذيباً ومذاباً؟', 'options': ['هواء واسم', 'ماء وسكر', 'ضوء وصوت', 'حرارة ووعاء'], 'answer': 1, 'hint': 'الماء يمكن أن يعمل كمذيب والسكر كمذاب.'}, {'id': 39, 'section_id': 'section3', 'text': 'لماذا تعد الروابط الهيدروجينية مهمة للماء؟', 'options': ['تحوّل الماء إلى معدن', 'تلغي قطبية الماء', 'تساعد في تفسير بعض خصائصه', 'تمنع وجود جزيئات الماء'], 'answer': 2, 'hint': 'الروابط الهيدروجينية تؤثر في خصائص الماء.'}, {'id': 40, 'section_id': 'section3', 'text': 'ما الفرق الأساسي بين المذيب والمذاب؟', 'options': ['المذاب يذيب دائماً والمذيب يذوب', 'كلاهما ضوء', 'لا يوجد فرق بينهما', 'المذيب يذيب والمذاب يذوب'], 'answer': 3, 'hint': 'تذكّر وظيفة كل مكوّن في المحلول.'}, {'id': 41, 'section_id': 'section4', 'text': 'لماذا يُعد الكربون مهماً في علم الأحياء؟', 'options': ['يدخل في تركيب معظم الجزيئات الحيوية', 'لا يكوّن أي روابط', 'يوجد في الضوء فقط', 'يمنع تكوّن الجزيئات'], 'answer': 0, 'hint': 'الكربون عنصر أساسي في الجزيئات الحيوية.'}, {'id': 42, 'section_id': 'section4', 'text': 'كم رابطة تساهمية يمكن لذرة الكربون تكوينها عادةً؟', 'options': ['رابطتان', 'أربع روابط', 'عشر روابط دائماً', 'رابطة واحدة'], 'answer': 1, 'hint': 'الكربون يستطيع تكوين أربع روابط تساهمية.'}, {'id': 43, 'section_id': 'section4', 'text': 'ما المقصود بالجزيئات الضخمة؟', 'options': ['ضوء متجمع', 'ماء نقي فقط', 'جزيئات كبيرة تتكوّن من وحدات أصغر', 'ذرات منفردة فقط'], 'answer': 2, 'hint': 'الجزيئات الضخمة كبيرة وقد تُبنى من وحدات أصغر.'}, {'id': 44, 'section_id': 'section4', 'text': 'أي مما يلي مجموعة من الجزيئات الضخمة الحيوية؟', 'options': ['الماء والضوء والصوت', 'الحرارة والغاز والوعاء', 'الإلكترونات فقط', 'الكربوهيدرات والدهون والبروتينات والأحماض النووية'], 'answer': 3, 'hint': 'تذكّر المجموعات الحيوية الأربع.'}, {'id': 45, 'section_id': 'section4', 'text': 'ما أحد أدوار الكربوهيدرات؟', 'options': ['مصدر للطاقة أو دعم هيكلي', 'منع كل التفاعلات', 'تكوين الضوء', 'إزالة جميع الذرات'], 'answer': 0, 'hint': 'السكريات مصدر للطاقة والسليلوز دعم هيكلي.'}, {'id': 46, 'section_id': 'section4', 'text': 'أي مادة مثال على الدعم الهيكلي في النباتات؟', 'options': ['الملح فقط', 'السليلوز', 'الأكسجين فقط', 'الضوء'], 'answer': 1, 'hint': 'السليلوز يدخل في جدران الخلايا النباتية.'}, {'id': 47, 'section_id': 'section4', 'text': 'ما نوع الروابط التي يكوّنها الكربون غالباً في الجزيئات الحيوية؟', 'options': ['روابط صوتية', 'لا يكوّن روابط', 'روابط تساهمية', 'روابط ضوئية'], 'answer': 2, 'hint': 'الكربون يشارك إلكترونات في روابط تساهمية.'}, {'id': 48, 'section_id': 'section4', 'text': 'أي عنصر يشكّل هيكلاً مهماً لكثير من الجزيئات الحيوية؟', 'options': ['الذهب فقط', 'الهيليوم فقط', 'الحديد دائماً', 'الكربون'], 'answer': 3, 'hint': 'الكربون أساس كثير من المركبات الحيوية.'}, {'id': 49, 'section_id': 'section4', 'text': 'أي من الآتي ليس من الجزيئات الضخمة الحيوية الأربع؟', 'options': ['الماء', 'الكربوهيدرات', 'البروتينات', 'الأحماض النووية'], 'answer': 0, 'hint': 'الماء مهم للحياة لكنه ليس ضمن المجموعات الأربع المذكورة هنا.'}, {'id': 50, 'section_id': 'section4', 'text': 'ما الوحدة البنائية التي قد تتكرر لتكوين جزيء ضخم؟', 'options': ['حرارة', 'وحدة أصغر أو مونومر', 'ضوء', 'وعاء'], 'answer': 1, 'hint': 'الجزيئات الكبيرة قد تتكون من وحدات متكررة.'}, {'id': 51, 'section_id': 'section4', 'text': 'ما وظيفة البروتينات في الكائنات الحية؟', 'options': ['تمنع كل التفاعلات', 'لا تحتوي على ذرات', 'لها أدوار بنائية ووظيفية متعددة', 'تنتج الضوء دائماً'], 'answer': 2, 'hint': 'البروتينات تؤدي وظائف عديدة في الخلايا.'}, {'id': 52, 'section_id': 'section4', 'text': 'ما وظيفة الأحماض النووية بشكل عام؟', 'options': ['إذابة جميع المعادن', 'تكوين الضوء', 'منع تكوّن الخلايا', 'تخزين ونقل المعلومات الوراثية'], 'answer': 3, 'hint': 'DNA وRNA مرتبطان بالمعلومات الوراثية.'}, {'id': 53, 'section_id': 'section4', 'text': 'أي جزيئات ترتبط غالباً بتخزين الطاقة على المدى الطويل؟', 'options': ['الدهون', 'الماء فقط', 'الأحماض النووية فقط', 'الأملاح فقط'], 'answer': 0, 'hint': 'الدهون من الجزيئات المرتبطة بتخزين الطاقة.'}, {'id': 54, 'section_id': 'section4', 'text': 'أي جزيئات تُعد مصدراً سريعاً شائعاً للطاقة؟', 'options': ['المعادن فقط', 'الكربوهيدرات', 'الزجاج', 'الضوء فقط'], 'answer': 1, 'hint': 'الكربوهيدرات يمكن أن توفر الطاقة.'}, {'id': 55, 'section_id': 'section4', 'text': 'ما سبب تنوع مركبات الكربون؟', 'options': ['وجوده في الماء فقط', 'كونه لا يتفاعل', 'قدرته على تكوين أربع روابط', 'عدم قدرته على الترابط'], 'answer': 2, 'hint': 'أربع روابط تسمح بتراكيب متنوعة.'}, {'id': 56, 'section_id': 'section4', 'text': 'أي عبارة عن الجزيئات الضخمة صحيحة؟', 'options': ['تتكوّن من الضوء فقط', 'لا توجد في الخلايا', 'كلها غازات', 'قد تتكوّن من وحدات أصغر'], 'answer': 3, 'hint': 'بعضها يُبنى من وحدات أصغر متكررة.'}, {'id': 57, 'section_id': 'section4', 'text': 'أي مجموعة تتضمن الدهون؟', 'options': ['الجزيئات الضخمة الحيوية', 'المذيبات فقط', 'العناصر المعدنية فقط', 'الغازات النقية فقط'], 'answer': 0, 'hint': 'الدهون إحدى المجموعات الحيوية الكبرى.'}, {'id': 58, 'section_id': 'section4', 'text': 'أي مجموعة تتضمن الكربوهيدرات؟', 'options': ['المحفزات غير الحيوية فقط', 'الجزيئات الضخمة الحيوية', 'الروابط الهيدروجينية فقط', 'الأملاح فقط'], 'answer': 1, 'hint': 'الكربوهيدرات من الجزيئات الحيوية الكبرى.'}, {'id': 59, 'section_id': 'section4', 'text': 'كيف يمكن للكربوهيدرات أن تساعد النبات؟', 'options': ['تمنع وجود الخلايا', 'تلغي الروابط الكيميائية', 'السليلوز يوفر دعماً هيكلياً', 'تحوّل كل الماء إلى ضوء'], 'answer': 2, 'hint': 'السليلوز يدعم تركيب النبات.'}, {'id': 60, 'section_id': 'section4', 'text': 'ما الفكرة الأساسية عن الكربون في الحياة؟', 'options': ['لا يمكنه تكوين روابط', 'يوجد خارج الكائنات فقط', 'لا يرتبط بأي عنصر', 'يمكنه تكوين تراكيب متنوعة تدخل في الجزيئات الحيوية'], 'answer': 3, 'hint': 'قدرة الكربون على الترابط تفسّر تنوع الجزيئات الحيوية.'}]



def get_completed_section_ids():
    connection = get_db()
    rows = connection.execute(
        "SELECT section_id FROM lesson_progress WHERE student_id = ? AND completed = 1",
        (session["student_id"],),
    ).fetchall()
    connection.close()
    return {row["section_id"] for row in rows}


# Keep the displayed question count synchronized with the actual question bank.
for section in LESSON_SECTIONS:
    section["question_count"] = sum(1 for question in QUESTIONS if question["section_id"] == section["id"])



@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        connection = get_db()

        teacher = connection.execute(
            "SELECT * FROM teachers WHERE username = ?", (username,)
        ).fetchone()
        if teacher and check_password_hash(teacher["password"], password):
            connection.close()
            session.clear()
            session["teacher_id"] = teacher["id"]
            session["username"] = teacher["username"]
            session["role"] = "teacher"
            return redirect(url_for("teacher_dashboard"))

        student = connection.execute(
            "SELECT * FROM students WHERE username = ?", (username,)
        ).fetchone()
        connection.close()
        if student and check_password_hash(student["password"], password):
            session.clear()
            session["student_id"] = student["id"]
            session["username"] = student["username"]
            session["grade"] = student["grade"]
            session["role"] = "student"
            return redirect(url_for(f"grade{student['grade']}"))
        error = "Incorrect username or password."
    return render_template("login.html", error=error)


@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher" or "teacher_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()
    students = connection.execute(
        """
        SELECT
            s.id, s.username, s.grade, s.points,
            (SELECT COUNT(*) FROM solved_questions sq WHERE sq.student_id = s.id) AS solved,
            (SELECT COUNT(*) FROM lesson_progress lp WHERE lp.student_id = s.id AND lp.completed = 1) AS sections_completed
        FROM students s
        ORDER BY s.grade, s.username
        """
    ).fetchall()

    feedback_rows = connection.execute(
        """
        SELECT sf.rating, sf.section_id, sf.created_at, s.username
        FROM section_feedback sf
        JOIN students s ON s.id = sf.student_id
        ORDER BY sf.created_at DESC
        LIMIT 12
        """
    ).fetchall()
    connection.close()

    student_rows = []
    for student in students:
        solved = student["solved"]
        percentage = round((solved / len(QUESTIONS)) * 100) if QUESTIONS else 0
        student_rows.append({
            "username": student["username"],
            "grade": student["grade"],
            "points": student["points"],
            "solved": solved,
            "percentage": percentage,
            "sections_completed": student["sections_completed"],
        })

    total_students = len(student_rows)
    total_questions_solved = sum(row["solved"] for row in student_rows)
    total_points = sum(row["points"] for row in student_rows)

    return render_template(
        "teacher.html",
        students=student_rows,
        feedback=feedback_rows,
        total_students=total_students,
        total_questions_solved=total_questions_solved,
        total_points=total_points,
        total_questions=len(QUESTIONS),
    )


@app.route("/grade9")
def grade9():
    if session.get("role") != "student" or "student_id" not in session or session.get("grade") != 9:
        return redirect(url_for("login"))
    connection = get_db()
    student = connection.execute(
        "SELECT points FROM students WHERE id = ?", (session["student_id"],)
    ).fetchone()
    completed = connection.execute(
        "SELECT COUNT(*) AS total FROM lesson_progress WHERE student_id = ? AND completed = 1 AND section_id IN ('section2','section3','section4')",
        (session["student_id"],),
    ).fetchone()["total"]
    correct_answers = connection.execute(
        "SELECT COUNT(*) AS total FROM solved_questions WHERE student_id = ? AND question_id BETWEEN 1 AND 60",
        (session["student_id"],),
    ).fetchone()["total"]
    total_percentage = round((correct_answers / len(QUESTIONS)) * 100) if QUESTIONS else 0
    connection.close()
    return render_template(
        "grade9.html",
        points=student["points"] if student else 0,
        completed=correct_answers,
        progress=total_percentage,
        sections_completed=completed,
        total_percentage=total_percentage,
    )


@app.route("/grade11")
def grade11():
    if session.get("role") != "student" or "student_id" not in session or session.get("grade") != 11:
        return redirect(url_for("login"))
    return render_template("grade11.html")


@app.route("/grade12")
def grade12():
    if session.get("role") != "student" or "student_id" not in session or session.get("grade") != 12:
        return redirect(url_for("login"))
    return render_template("grade12.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def get_solved_question_ids():
    connection = get_db()
    rows = connection.execute(
        "SELECT question_id FROM solved_questions WHERE student_id = ?",
        (session["student_id"],),
    ).fetchall()
    connection.close()
    return [row["question_id"] for row in rows]


def get_feedback_section_ids():
    connection = get_db()
    rows = connection.execute(
        "SELECT section_id FROM section_feedback WHERE student_id = ?",
        (session["student_id"],),
    ).fetchall()
    connection.close()
    return {row["section_id"] for row in rows}


@app.route("/grade9/biology/lesson1")
def biology_lesson1():
    if session.get("role") != "student" or "student_id" not in session or session.get("grade") != 9:
        return redirect(url_for("login"))
    return render_template(
        "lesson1.html",
        sections=LESSON_SECTIONS,
        questions=QUESTIONS,
        completed_ids=get_completed_section_ids(),
        solved_question_ids=get_solved_question_ids(),
        feedback_section_ids=get_feedback_section_ids(),
        result=None,
    )


def get_section_statistics(student_id, section_id):
    question_ids = [q["id"] for q in QUESTIONS if q["section_id"] == section_id]
    total = len(question_ids)
    if not total:
        return {"total": 0, "first_correct": 0, "first_wrong": 0, "second_correct": 0, "second_wrong": 0, "third_correct": 0, "third_wrong": 0, "fourth_plus_correct": 0, "fourth_plus_wrong": 0, "overall": 0}
    connection = get_db()
    rows = connection.execute(
        "SELECT attempt_number, correct, COUNT(*) AS total FROM question_attempts WHERE student_id = ? AND question_id IN (" + ",".join("?" for _ in question_ids) + ") GROUP BY attempt_number, correct",
        [student_id, *question_ids],
    ).fetchall()
    connection.close()
    stats = {"first_correct": 0, "first_wrong": 0, "second_correct": 0, "second_wrong": 0, "third_correct": 0, "third_wrong": 0, "fourth_plus_correct": 0, "fourth_plus_wrong": 0}
    for row in rows:
        n = row["attempt_number"]
        key = "first" if n == 1 else "second" if n == 2 else "third" if n == 3 else "fourth_plus"
        result = "correct" if row["correct"] else "wrong"
        stats[f"{key}_{result}"] += row["total"]
    stats["total"] = total

    # Overall section percentage is based on HOW the student solved each
    # question, not simply on whether it was eventually correct.
    # 1st try = 100%, 2nd try = 80%, 3rd try = 60%, 4th+ try = 40%.
    # This guarantees that 100% is possible only when every question was
    # answered correctly on the first attempt.
    connection = get_db()
    earliest_rows = connection.execute(
        "SELECT question_id, MIN(CASE WHEN correct = 1 THEN attempt_number END) AS correct_attempt "
        "FROM question_attempts WHERE student_id = ? AND question_id IN (" + ",".join("?" for _ in question_ids) + ") "
        "GROUP BY question_id",
        [student_id, *question_ids],
    ).fetchall()
    connection.close()

    weights = {1: 100, 2: 80, 3: 60}
    weighted_total = 0
    for row in earliest_rows:
        attempt = row["correct_attempt"]
        if attempt is not None:
            weighted_total += weights.get(attempt, 40)
    stats["overall"] = round(weighted_total / total)

    for key in list(stats):
        if key not in {"total", "overall"}:
            stats[key + "_percent"] = round(stats[key] / total * 100)
    return stats


@app.route("/grade9/biology/lesson1/answer", methods=["POST"])
def check_lesson_answer():
    if session.get("role") != "student" or "student_id" not in session or session.get("grade") != 9:
        return jsonify({"ok": False, "message": "غير مصرح"}), 401
    data = request.get_json(silent=True) or {}
    try:
        question_id = int(data.get("question_id"))
        selected_index = int(data.get("answer"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "إجابة غير صالحة"}), 400
    question = next((q for q in QUESTIONS if q["id"] == question_id), None)
    if question is None or selected_index < 0 or selected_index >= len(question["options"]):
        return jsonify({"ok": False, "message": "السؤال أو الإجابة غير صالحة"}), 400

    student_id = session["student_id"]
    connection = get_db()
    already_solved = connection.execute(
        "SELECT 1 FROM solved_questions WHERE student_id = ? AND question_id = ?",
        (student_id, question_id),
    ).fetchone() is not None
    if already_solved:
        connection.close()
        return jsonify({"ok": True, "correct": True, "awarded": False, "already_solved": True, "hint": question["hint"]})

    attempt_number = connection.execute(
        "SELECT COALESCE(MAX(attempt_number), 0) + 1 AS next_attempt FROM question_attempts WHERE student_id = ? AND question_id = ?",
        (student_id, question_id),
    ).fetchone()["next_attempt"]
    correct = selected_index == question["answer"]
    connection.execute(
        "INSERT INTO question_attempts (student_id, question_id, attempt_number, selected_index, correct) VALUES (?, ?, ?, ?, ?)",
        (student_id, question_id, attempt_number, selected_index, int(correct)),
    )

    awarded = False
    if correct:
        connection.execute(
            "INSERT OR IGNORE INTO solved_questions (student_id, question_id) VALUES (?, ?)",
            (student_id, question_id),
        )
        already_awarded = connection.execute(
            "SELECT 1 FROM question_points WHERE student_id = ? AND question_id = ?",
            (student_id, question_id),
        ).fetchone()
        if not already_awarded:
            connection.execute(
                "INSERT INTO question_points (student_id, question_id, points) VALUES (?, ?, 10)",
                (student_id, question_id),
            )
            connection.execute("UPDATE students SET points = points + 10 WHERE id = ?", (student_id,))
            awarded = True

    section_question_ids = [q["id"] for q in QUESTIONS if q["section_id"] == question["section_id"]]
    solved_count = connection.execute(
        "SELECT COUNT(*) AS total FROM solved_questions WHERE student_id = ? AND question_id IN (" + ",".join("?" for _ in section_question_ids) + ")",
        [student_id, *section_question_ids],
    ).fetchone()["total"]
    section_completed = solved_count == len(section_question_ids)
    feedback_given = connection.execute(
        "SELECT 1 FROM section_feedback WHERE student_id = ? AND section_id = ?",
        (student_id, question["section_id"]),
    ).fetchone() is not None
    if section_completed:
        connection.execute(
            "INSERT OR IGNORE INTO lesson_progress (student_id, section_id, completed) VALUES (?, ?, 1)",
            (student_id, question["section_id"]),
        )
    connection.commit()
    connection.close()

    stats = get_section_statistics(student_id, question["section_id"]) if section_completed else None
    return jsonify({
        "ok": True,
        "correct": correct,
        "awarded": awarded,
        "attempt_number": attempt_number,
        "hint": question["hint"],
        "section_completed": section_completed,
        "section_id": question["section_id"],
        "feedback_given": feedback_given,
        "section_stats": stats,
    })


@app.route("/grade9/biology/lesson1/feedback", methods=["POST"])
def save_section_feedback():
    if session.get("role") != "student" or "student_id" not in session or session.get("grade") != 9:
        return jsonify({"ok": False, "message": "غير مصرح"}), 401
    data = request.get_json(silent=True) or {}
    section_id = str(data.get("section_id", "")).strip()
    rating = str(data.get("rating", "")).strip()
    valid_sections = {section["id"] for section in LESSON_SECTIONS}
    if section_id not in valid_sections or rating not in {"happy", "neutral", "angry"}:
        return jsonify({"ok": False, "message": "بيانات غير صالحة"}), 400

    connection = get_db()
    solved_count = connection.execute(
        "SELECT COUNT(*) AS total FROM solved_questions WHERE student_id = ? AND question_id IN ("
        + ",".join("?" for _ in [q for q in QUESTIONS if q["section_id"] == section_id]) + ")",
        [session["student_id"]] + [q["id"] for q in QUESTIONS if q["section_id"] == section_id],
    ).fetchone()["total"]
    required_count = sum(1 for q in QUESTIONS if q["section_id"] == section_id)
    if solved_count < required_count:
        connection.close()
        return jsonify({"ok": False, "message": "لم يكتمل القسم بعد"}), 400

    connection.execute(
        "INSERT OR IGNORE INTO section_feedback (student_id, section_id, rating) VALUES (?, ?, ?)",
        (session["student_id"], section_id, rating),
    )
    connection.commit()
    connection.close()
    stats = get_section_statistics(session["student_id"], section_id)
    return jsonify({"ok": True, "stats": stats, "redirect": url_for("grade9")})


@app.route("/grade9/biology/lesson1/exam", methods=["POST"])
def submit_lesson_exam():
    if session.get("role") != "student" or "student_id" not in session or session.get("grade") != 9:
        return redirect(url_for("login"))

    score = 0
    feedback = []
    connection = get_db()

    for question in QUESTIONS:
        selected = request.form.get(f"question_{question['id']}")
        try:
            selected_index = int(selected) if selected is not None else None
        except (TypeError, ValueError):
            selected_index = None
        correct = selected_index is not None and selected_index == question["answer"]
        if correct:
            score += 1
            already_awarded = connection.execute(
                "SELECT 1 FROM question_points WHERE student_id = ? AND question_id = ?",
                (session["student_id"], question["id"]),
            ).fetchone()
            if not already_awarded:
                connection.execute(
                    "INSERT INTO question_points (student_id, question_id, points) VALUES (?, ?, 10)",
                    (session["student_id"], question["id"]),
                )
                connection.execute(
                    "UPDATE students SET points = points + 10 WHERE id = ?",
                    (session["student_id"],),
                )
        feedback.append({
            "question_number": question["id"],
            "correct": correct,
            "hint": question["hint"],
        })

    total = len(QUESTIONS)
    passing_score = 42
    passed = score >= passing_score
    newly_completed = False

    if passed:
        existing = connection.execute(
            "SELECT completed FROM lesson_progress WHERE student_id = ? AND section_id = ?",
            (session["student_id"], "lesson1_exam"),
        ).fetchone()
        if not existing:
            connection.execute(
                "INSERT INTO lesson_progress (student_id, section_id, completed) VALUES (?, ?, 1)",
                (session["student_id"], "lesson1_exam"),
            )
            newly_completed = True

    connection.commit()
    connection.close()

    result = {
        "score": score,
        "total": total,
        "passing_score": passing_score,
        "passed": passed,
        "newly_completed": newly_completed,
        "feedback": feedback,
    }
    return render_template(
        "lesson1.html",
        sections=LESSON_SECTIONS,
        questions=QUESTIONS,
        completed_ids=get_completed_section_ids(),
        solved_question_ids=get_solved_question_ids(),
        feedback_section_ids=get_feedback_section_ids(),
        result=result,
    )


if __name__ == "__main__":
    create_database()
    app.run(debug=True)
