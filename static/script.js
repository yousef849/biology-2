// ========================================
// LOGIN INTERACTIONS
// ========================================

const password = document.getElementById("password");
const showPassword = document.getElementById("showPassword");
const rememberMe = document.getElementById("rememberMe");
const username = document.getElementById("username");
const form = document.getElementById("loginForm");
const loginCard = document.querySelector(".bioquest-login-card");

if (showPassword && password) {
    showPassword.addEventListener("click", function () {
        const visible = password.type === "password";
        password.type = visible ? "text" : "password";
        showPassword.textContent = visible ? "🙈" : "👁";
        showPassword.setAttribute("aria-label", visible ? "Hide password" : "Show password");
    });
}

if (username && rememberMe) {
    const savedUsername = localStorage.getItem("rememberedUsername");
    if (savedUsername) {
        username.value = savedUsername;
        rememberMe.checked = true;
    }
}

if (form && username && rememberMe) {
    form.addEventListener("submit", function () {
        if (rememberMe.checked) {
            localStorage.setItem("rememberedUsername", username.value);
        } else {
            localStorage.removeItem("rememberedUsername");
        }
    });
}

// Localized required-field validation. This replaces the browser's default
// "Please fill out this field" message with the language selected in BioQuest.
function getCurrentBioQuestLanguage() {
    return localStorage.getItem("bioquestLanguage") || "en";
}

function getRequiredFieldMessage(lang, field) {
    const messages = {
        en: { username: "Please enter your username.", password: "Please enter your password." },
        ar: { username: "يرجى إدخال اسم المستخدم.", password: "يرجى إدخال كلمة المرور." },
        es: { username: "Por favor, escribe tu nombre de usuario.", password: "Por favor, escribe tu contraseña." }
    };
    return (messages[lang] || messages.en)[field];
}

if (form && username && password) {
    form.setAttribute("novalidate", "novalidate");

    const requiredFields = [username, password];
    requiredFields.forEach((field) => {
        field.addEventListener("input", () => field.setCustomValidity(""));
    });

    form.addEventListener("submit", function (event) {
        requiredFields.forEach((field) => field.setCustomValidity(""));

        const lang = getCurrentBioQuestLanguage();
        let firstInvalid = null;

        if (!username.value.trim()) {
            username.setCustomValidity(getRequiredFieldMessage(lang, "username"));
            firstInvalid = firstInvalid || username;
        }

        if (!password.value) {
            password.setCustomValidity(getRequiredFieldMessage(lang, "password"));
            firstInvalid = firstInvalid || password;
        }

        if (firstInvalid) {
            event.preventDefault();
            firstInvalid.reportValidity();
            firstInvalid.focus();
            return;
        }

        if (rememberMe && rememberMe.checked) {
            localStorage.setItem("rememberedUsername", username.value);
        } else {
            localStorage.removeItem("rememberedUsername");
        }
    });
}

// Subtle 3D card movement follows the pointer on the login page.
if (loginCard && window.matchMedia("(prefers-reduced-motion: no-preference)").matches) {
    loginCard.addEventListener("mousemove", (event) => {
        const rect = loginCard.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - 0.5;
        const y = (event.clientY - rect.top) / rect.height - 0.5;
        loginCard.style.transform = `perspective(1100px) rotateX(${(-y * 2.2).toFixed(2)}deg) rotateY(${(x * 2.2).toFixed(2)}deg) translateY(-4px)`;
    });

    loginCard.addEventListener("mouseleave", () => {
        loginCard.style.transform = "";
    });
}

// Animated cursor glow on the login scene.
const loginScene = document.querySelector(".login-scene");
if (loginScene) {
    loginScene.addEventListener("pointermove", (event) => {
        loginScene.style.setProperty("--mouse-x", `${event.clientX}px`);
        loginScene.style.setProperty("--mouse-y", `${event.clientY}px`);
    });
}

// Add a quick press animation without blocking the real Flask form submission.
const loginButton = document.querySelector(".bioquest-login-btn");
if (loginButton) {
    loginButton.addEventListener("click", () => {
        loginButton.classList.remove("login-pressed");
        requestAnimationFrame(() => loginButton.classList.add("login-pressed"));
    });
}

// ========================================
// BIOQUEST LANGUAGE SWITCHER
// ========================================

const bioquestTranslations = {
    en: {
        language: "LANGUAGE",
        biologyLearning: "BIOLOGY LEARNING",
        tagline: "Learn • Explore • Level Up",
        subtitle: "Your next biology challenge is waiting.",
        usernameLabel: "Username",
        usernamePlaceholder: "Enter your username",
        passwordLabel: "Password",
        passwordPlaceholder: "Enter your password",
        showPassword: "Show password",
        hidePassword: "Hide password",
        remember: "Remember me",
        ready: "🧬 Ready to learn",
        enterBioquest: "Enter BioQuest",
        teacherNote: "Your teacher will provide your username and password.",
        dashboard: "Dashboard",
        biology: "Biology",
        rewards: "Rewards",
        progress: "Progress",
        logout: "Log out",
        studentDashboard: "STUDENT DASHBOARD",
        welcomeBack: "Welcome back! 👋",
        grade: "Grade",
        yourPoints: "Your Points",
        questionsSolved: "Questions Solved",
        progressLabel: "Progress",
        yourClass: "YOUR CLASS",
        grade9Biology: "Grade 9 Biology",
        biologyFundamentals: "Biology Fundamentals",
        biologyDescription: "Explore cells, living organisms, the human body, ecosystems, and other important Grade 9 biology topics.",
        courseProgress: "Course progress",
        startBiology: "Start Biology →",
        rewardsLabel: "REWARDS",
        earnRedeem: "Earn & Redeem",
        viewAll: "View all →",
        gymSubscription: "Gym Subscription",
        specialPrize: "Special Prize",
        comingSoon: "Coming soon"
    },
    ar: {
        language: "اللغة",
        biologyLearning: "تعلّم الأحياء",
        tagline: "تعلّم • استكشف • تطوّر",
        subtitle: "تحدّي الأحياء القادم بانتظارك.",
        usernameLabel: "اسم المستخدم",
        usernamePlaceholder: "أدخل اسم المستخدم",
        passwordLabel: "كلمة المرور",
        passwordPlaceholder: "أدخل كلمة المرور",
        showPassword: "إظهار كلمة المرور",
        hidePassword: "إخفاء كلمة المرور",
        remember: "تذكّرني",
        ready: "🧬 جاهز للتعلّم",
        enterBioquest: "دخول BioQuest",
        teacherNote: "سيزوّدك معلمك باسم المستخدم وكلمة المرور.",
        dashboard: "لوحة التحكم",
        biology: "الأحياء",
        rewards: "المكافآت",
        progress: "التقدم",
        logout: "تسجيل الخروج",
        studentDashboard: "لوحة الطالب",
        welcomeBack: "مرحباً بعودتك! 👋",
        grade: "الصف",
        yourPoints: "نقاطك",
        questionsSolved: "الأسئلة المحلولة",
        progressLabel: "التقدم",
        yourClass: "فصلك",
        grade9Biology: "أحياء الصف التاسع",
        biologyFundamentals: "أساسيات علم الأحياء",
        biologyDescription: "استكشف الخلايا والكائنات الحية وجسم الإنسان والأنظمة البيئية وغيرها من موضوعات الأحياء المهمة للصف التاسع.",
        courseProgress: "تقدم المقرر",
        startBiology: "ابدأ الأحياء ←",
        rewardsLabel: "المكافآت",
        earnRedeem: "اكسب واستبدل",
        viewAll: "عرض الكل ←",
        gymSubscription: "اشتراك النادي الرياضي",
        specialPrize: "جائزة خاصة",
        comingSoon: "قريباً"
    },
    es: {
        language: "IDIOMA",
        biologyLearning: "APRENDIZAJE DE BIOLOGÍA",
        tagline: "Aprende • Explora • Avanza",
        subtitle: "Tu próximo desafío de biología te está esperando.",
        usernameLabel: "Nombre de usuario",
        usernamePlaceholder: "Escribe tu nombre de usuario",
        passwordLabel: "Contraseña",
        passwordPlaceholder: "Escribe tu contraseña",
        showPassword: "Mostrar contraseña",
        hidePassword: "Ocultar contraseña",
        remember: "Recordarme",
        ready: "🧬 Listo para aprender",
        enterBioquest: "Entrar en BioQuest",
        teacherNote: "Tu profesor te dará tu nombre de usuario y contraseña.",
        dashboard: "Panel",
        biology: "Biología",
        rewards: "Recompensas",
        progress: "Progreso",
        logout: "Cerrar sesión",
        studentDashboard: "PANEL DEL ESTUDIANTE",
        welcomeBack: "¡Bienvenido de nuevo! 👋",
        grade: "Grado",
        yourPoints: "Tus puntos",
        questionsSolved: "Preguntas resueltas",
        progressLabel: "Progreso",
        yourClass: "TU CLASE",
        grade9Biology: "Biología de 9.º grado",
        biologyFundamentals: "Fundamentos de Biología",
        biologyDescription: "Explora las células, los seres vivos, el cuerpo humano, los ecosistemas y otros temas importantes de biología de 9.º grado.",
        courseProgress: "Progreso del curso",
        startBiology: "Empezar Biología →",
        rewardsLabel: "RECOMPENSAS",
        earnRedeem: "Gana y canjea",
        viewAll: "Ver todo →",
        gymSubscription: "Suscripción al gimnasio",
        specialPrize: "Premio especial",
        comingSoon: "Próximamente"
    }
};

const bioquestQuotes = {
    en: {
        q1: '“The more you explore life, the more fascinating it becomes.”',
        q2: '“Every cell has a story worth discovering.”',
        q3: '“Curiosity is the first step to understanding biology.”',
        q4: '“Learn. Explore. Discover.”',
        q5: '“Science begins with a question.”',
        q6: '“Your next discovery starts here.”'
    },
    ar: {
        q1: '“كلما استكشفت الحياة أكثر، أصبحت أكثر إثارة.”',
        q2: '“كل خلية تحمل قصة تستحق الاكتشاف.”',
        q3: '“الفضول هو الخطوة الأولى لفهم علم الأحياء.”',
        q4: '“تعلّم. استكشف. اكتشف.”',
        q5: '“العلم يبدأ بسؤال.”',
        q6: '“اكتشافك القادم يبدأ من هنا.”'
    },
    es: {
        q1: '“Cuanto más exploras la vida, más fascinante se vuelve.”',
        q2: '“Cada célula tiene una historia por descubrir.”',
        q3: '“La curiosidad es el primer paso para entender la biología.”',
        q4: '“Aprende. Explora. Descubre.”',
        q5: '“La ciencia comienza con una pregunta.”',
        q6: '“Tu próximo descubrimiento empieza aquí.”'
    }
};

function setBioQuestLanguage(lang) {
    const dictionary = bioquestTranslations[lang] || bioquestTranslations.en;
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    document.body.classList.toggle("arabic-ui", lang === "ar");

    document.querySelectorAll("[data-i18n]").forEach((element) => {
        const key = element.dataset.i18n;
        if (dictionary[key] !== undefined) element.textContent = dictionary[key];
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
        const key = element.dataset.i18nPlaceholder;
        if (dictionary[key] !== undefined) element.placeholder = dictionary[key];
    });

    document.querySelectorAll("[data-i18n-aria]").forEach((element) => {
        const key = element.dataset.i18nAria;
        if (dictionary[key] !== undefined) element.setAttribute("aria-label", dictionary[key]);
    });

    document.querySelectorAll(".language-btn").forEach((button) => {
        button.classList.toggle("active", button.dataset.lang === lang);
    });

    document.querySelectorAll(".quote[data-quote-key]").forEach((quote) => {
        const key = quote.dataset.quoteKey;
        if (bioquestQuotes[lang] && bioquestQuotes[lang][key]) {
            quote.textContent = bioquestQuotes[lang][key];
        }
    });

    localStorage.setItem("bioquestLanguage", lang);
    document.title = lang === "ar"
        ? "BioQuest — تعلّم • استكشف • تطوّر"
        : lang === "es"
            ? "BioQuest — Aprende • Explora • Avanza"
            : "BioQuest — Learn • Explore • Level Up";

    // Keep the password accessibility label in sync if it is currently visible.
    if (showPassword && password && password.type === "text") {
        showPassword.setAttribute("aria-label", dictionary.hidePassword);
    }
}

const languageButtons = document.querySelectorAll(".language-btn");
if (languageButtons.length) {
    const savedLanguage = localStorage.getItem("bioquestLanguage") || "en";
    setBioQuestLanguage(savedLanguage);

    languageButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const lang = button.dataset.lang;
            setBioQuestLanguage(lang);
        });
    });
}
