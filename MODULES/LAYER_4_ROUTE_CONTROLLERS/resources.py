from flask import Blueprint, render_template, redirect, session

resources_bp = Blueprint('resources_bp', __name__)

COMPANY_HUB = [
    {
        "key": "google",
        "name": "Google",
        "color": "#4285F4",
        "description": "Data Structures, Algorithms, System Design, and Behavioral questions frequently asked at Google interviews.",
        "total_questions": 4,
        "resources": [
            {"site": "LeetCode",      "label": "Google Tagged Problems",       "desc": "Filter and solve coding problems tagged specifically for Google — sorted by frequency and difficulty.",          "url": "https://leetcode.com/company/google/",                           "icon": "bi-code-slash"},
            {"site": "GeeksForGeeks", "label": "Google Interview Questions",   "desc": "Topic-wise DSA prep, system design guides, and real interview experiences shared by Google candidates.",        "url": "https://www.geeksforgeeks.org/google-interview-preparation/",    "icon": "bi-mortarboard-fill"},
            {"site": "PrepInsta",     "label": "Google Placement Papers",      "desc": "Aptitude rounds, coding tests, and placement paper patterns based on past Google recruitment drives.",          "url": "https://prepinsta.com/google/",                                  "icon": "bi-file-earmark-text-fill"},
            {"site": "InterviewBit",  "label": "Google Interview Prep",        "desc": "Structured mock interviews, real Q&A from candidates, and company-specific preparation guides.",               "url": "https://www.interviewbit.com/google-interview-questions/",       "icon": "bi-chat-left-dots-fill"},
        ],
    },
    {
        "key": "microsoft",
        "name": "Microsoft",
        "color": "#00A4EF",
        "description": "OOP, OS, Networking, and problem-solving questions asked across SDE and SDET roles at Microsoft.",
        "total_questions": 4,
        "resources": [
            {"site": "LeetCode",      "label": "Microsoft Tagged Problems",     "desc": "Practice the most frequently asked coding problems tagged for Microsoft SDE and SDET roles.",                  "url": "https://leetcode.com/company/microsoft/",                        "icon": "bi-code-slash"},
            {"site": "GeeksForGeeks", "label": "Microsoft Interview Questions", "desc": "Round-wise preparation guide, interview experiences, and topic coverage for Microsoft placements.",            "url": "https://www.geeksforgeeks.org/microsoft-interview-preparation/", "icon": "bi-mortarboard-fill"},
            {"site": "PrepInsta",     "label": "Microsoft Placement Papers",    "desc": "Aptitude test patterns, coding round formats, and previous year placement papers from Microsoft.",             "url": "https://prepinsta.com/microsoft/",                               "icon": "bi-file-earmark-text-fill"},
            {"site": "InterviewBit",  "label": "Microsoft Interview Prep",      "desc": "Real interview experiences, mock tests, and structured question sets for Microsoft roles.",                    "url": "https://www.interviewbit.com/microsoft-interview-questions/",    "icon": "bi-chat-left-dots-fill"},
        ],
    },
    {
        "key": "amazon",
        "name": "Amazon",
        "color": "#FF9900",
        "description": "Leadership Principles, problem-solving, system design, and behavioral rounds for Amazon SDE roles.",
        "total_questions": 4,
        "resources": [
            {"site": "LeetCode",      "label": "Amazon Tagged Problems",        "desc": "Solve the most frequently asked Amazon SDE problems, filtered by topic and difficulty level.",                 "url": "https://leetcode.com/company/amazon/",                           "icon": "bi-code-slash"},
            {"site": "GeeksForGeeks", "label": "Amazon Interview Questions",    "desc": "Comprehensive preparation covering DSA, Leadership Principles, system design, and past experiences.",          "url": "https://www.geeksforgeeks.org/amazon-interview-preparation/",    "icon": "bi-mortarboard-fill"},
            {"site": "PrepInsta",     "label": "Amazon Placement Papers",       "desc": "Amazon online assessment patterns, aptitude questions, and coding test formats from recent drives.",           "url": "https://prepinsta.com/amazon/",                                  "icon": "bi-file-earmark-text-fill"},
            {"site": "InterviewBit",  "label": "Amazon Interview Prep",         "desc": "Behavioral question bank aligned to Amazon Leadership Principles plus technical DSA prep.",                    "url": "https://www.interviewbit.com/amazon-interview-questions/",       "icon": "bi-chat-left-dots-fill"},
        ],
    },
    {
        "key": "meta",
        "name": "Meta (Facebook)",
        "color": "#1877F2",
        "description": "Graphs, Dynamic Programming, system design at scale, and product sense questions asked at Meta.",
        "total_questions": 4,
        "resources": [
            {"site": "LeetCode",      "label": "Meta Tagged Problems",          "desc": "Top Meta/Facebook-tagged coding problems covering graphs, DP, and array manipulations.",                       "url": "https://leetcode.com/company/facebook/",                         "icon": "bi-code-slash"},
            {"site": "GeeksForGeeks", "label": "Meta Interview Questions",      "desc": "Interview experiences, system design at scale concepts, and topic-wise guides for Meta.",                      "url": "https://www.geeksforgeeks.org/facebook-interview-preparation/",  "icon": "bi-mortarboard-fill"},
            {"site": "PrepInsta",     "label": "Meta Placement Papers",         "desc": "Aptitude and coding round patterns from Meta campus and off-campus recruitment drives.",                       "url": "https://prepinsta.com/facebook/",                                "icon": "bi-file-earmark-text-fill"},
            {"site": "InterviewBit",  "label": "Meta Interview Prep",           "desc": "Real Meta interview Q&A, mock assessments, and tips from candidates who cracked the process.",                "url": "https://www.interviewbit.com/facebook-interview-questions/",     "icon": "bi-chat-left-dots-fill"},
        ],
    },
    {
        "key": "netflix",
        "name": "Netflix",
        "color": "#E50914",
        "description": "Distributed systems, microservices, system design, and culture-fit questions asked at Netflix.",
        "total_questions": 4,
        "resources": [
            {"site": "LeetCode",      "label": "Netflix Tagged Problems",       "desc": "Netflix-tagged coding problems focusing on system design and complex algorithmic challenges.",                  "url": "https://leetcode.com/company/netflix/",                          "icon": "bi-code-slash"},
            {"site": "GeeksForGeeks", "label": "Netflix Interview Questions",   "desc": "Distributed systems, microservices architecture concepts, and interview experience guides.",                   "url": "https://www.geeksforgeeks.org/netflix-interview-questions/",     "icon": "bi-mortarboard-fill"},
            {"site": "PrepInsta",     "label": "Netflix Placement Papers",      "desc": "Placement test formats, aptitude rounds, and coding assessment patterns from Netflix drives.",                 "url": "https://prepinsta.com/netflix/",                                 "icon": "bi-file-earmark-text-fill"},
            {"site": "InterviewBit",  "label": "Netflix Interview Prep",        "desc": "System design deep dives, culture-fit Q&A, and mock interview practice for Netflix roles.",                   "url": "https://www.interviewbit.com/netflix-interview-questions/",      "icon": "bi-chat-left-dots-fill"},
        ],
    },
    {
        "key": "tcs",
        "name": "TCS",
        "color": "#00579C",
        "description": "Aptitude, verbal, logical reasoning, and coding questions for TCS NQT and campus drives.",
        "total_questions": 4,
        "resources": [
            {"site": "PrepInsta",     "label": "TCS NQT Placement Papers",      "desc": "Full TCS NQT mock tests, aptitude papers, verbal ability, and coding round preparation.",                     "url": "https://prepinsta.com/tcs/",                                     "icon": "bi-file-earmark-text-fill"},
            {"site": "GeeksForGeeks", "label": "TCS Interview Questions",       "desc": "Topic-wise preparation guide, HR round questions, and technical interview experiences for TCS.",               "url": "https://www.geeksforgeeks.org/tcs-interview-experience/",        "icon": "bi-mortarboard-fill"},
            {"site": "IndiaBix",      "label": "TCS Aptitude Practice",         "desc": "Quantitative aptitude, logical reasoning, and verbal practice sets matched to TCS NQT patterns.",             "url": "https://www.indiabix.com/",                                      "icon": "bi-calculator-fill"},
            {"site": "InterviewBit",  "label": "TCS Interview Prep",            "desc": "TCS-specific mock tests, real interview Q&A, and structured coding practice for campus drives.",              "url": "https://www.interviewbit.com/tcs-interview-questions/",          "icon": "bi-chat-left-dots-fill"},
        ],
    },
    {
        "key": "infosys",
        "name": "Infosys",
        "color": "#007CC3",
        "description": "Aptitude, reasoning, verbal, and coding questions for Infosys InfyTQ and Springboard assessments.",
        "total_questions": 4,
        "resources": [
            {"site": "PrepInsta",     "label": "Infosys Placement Papers",      "desc": "Mock tests for Infosys online aptitude rounds, verbal sections, and coding challenges.",                      "url": "https://prepinsta.com/infosys/",                                 "icon": "bi-file-earmark-text-fill"},
            {"site": "GeeksForGeeks", "label": "Infosys Interview Questions",   "desc": "Interview experiences, HR round preparation, and topic-wise technical prep for Infosys roles.",               "url": "https://www.geeksforgeeks.org/infosys-interview-experience/",    "icon": "bi-mortarboard-fill"},
            {"site": "InfyTQ",        "label": "Infosys InfyTQ Platform",       "desc": "Official Infosys learning and certification platform — complete courses and mock assessments.",               "url": "https://www.infytq.com/",                                        "icon": "bi-award-fill"},
            {"site": "InterviewBit",  "label": "Infosys Interview Prep",        "desc": "Real interview Q&A from Infosys candidates, aptitude practice, and placement preparation tips.",              "url": "https://www.interviewbit.com/infosys-interview-questions/",      "icon": "bi-chat-left-dots-fill"},
        ],
    },
    {
        "key": "wipro",
        "name": "Wipro",
        "color": "#4CAF50",
        "description": "Aptitude, reasoning, verbal ability, and coding assessments for Wipro NLTH and campus placements.",
        "total_questions": 4,
        "resources": [
            {"site": "PrepInsta",     "label": "Wipro NLTH Placement Papers",   "desc": "Wipro NLTH mock tests, aptitude patterns, written communication, and coding round prep.",                    "url": "https://prepinsta.com/wipro/",                                   "icon": "bi-file-earmark-text-fill"},
            {"site": "GeeksForGeeks", "label": "Wipro Interview Questions",     "desc": "Interview experiences, technical Q&A, and preparation guides for Wipro placement rounds.",                    "url": "https://www.geeksforgeeks.org/wipro-interview-experience/",      "icon": "bi-mortarboard-fill"},
            {"site": "IndiaBix",      "label": "Wipro Aptitude Practice",       "desc": "Quantitative aptitude, logical reasoning, and verbal ability practice aligned to Wipro patterns.",           "url": "https://www.indiabix.com/",                                      "icon": "bi-calculator-fill"},
            {"site": "InterviewBit",  "label": "Wipro Interview Prep",          "desc": "Wipro-specific mock interviews, HR round tips, and structured technical preparation.",                        "url": "https://www.interviewbit.com/wipro-interview-questions/",        "icon": "bi-chat-left-dots-fill"},
        ],
    },
    {
        "key": "accenture",
        "name": "Accenture",
        "color": "#A100FF",
        "description": "Cognitive ability, verbal, logical, and communication-focused questions for Accenture campus drives.",
        "total_questions": 4,
        "resources": [
            {"site": "PrepInsta",     "label": "Accenture Placement Papers",    "desc": "Accenture mock tests covering cognitive ability, verbal reasoning, and communication rounds.",                 "url": "https://prepinsta.com/accenture/",                               "icon": "bi-file-earmark-text-fill"},
            {"site": "GeeksForGeeks", "label": "Accenture Interview Questions", "desc": "Interview experiences, HR round Q&A, and technical preparation guides for Accenture placements.",             "url": "https://www.geeksforgeeks.org/accenture-interview-experience/",  "icon": "bi-mortarboard-fill"},
            {"site": "IndiaBix",      "label": "Accenture Aptitude Practice",   "desc": "Quantitative aptitude and logical reasoning practice sets matched to Accenture test patterns.",              "url": "https://www.indiabix.com/",                                      "icon": "bi-calculator-fill"},
            {"site": "InterviewBit",  "label": "Accenture Interview Prep",      "desc": "Real Accenture interview Q&A, placement tips, and mock rounds from recent campus candidates.",               "url": "https://www.interviewbit.com/accenture-interview-questions/",    "icon": "bi-chat-left-dots-fill"},
        ],
    },
    {
        "key": "cognizant",
        "name": "Cognizant",
        "color": "#1565C0",
        "description": "Aptitude, coding, verbal, and HR round questions for Cognizant GenC, GenC Next, and campus drives.",
        "total_questions": 4,
        "resources": [
            {"site": "PrepInsta",     "label": "Cognizant Placement Papers",    "desc": "Cognizant GenC and GenC Next mock tests, aptitude papers, and coding challenge preparation.",                "url": "https://prepinsta.com/cognizant/",                               "icon": "bi-file-earmark-text-fill"},
            {"site": "GeeksForGeeks", "label": "Cognizant Interview Questions", "desc": "Interview experiences, topic-wise prep, and HR round guidance for Cognizant campus placements.",              "url": "https://www.geeksforgeeks.org/cognizant-interview-experience/",  "icon": "bi-mortarboard-fill"},
            {"site": "IndiaBix",      "label": "Cognizant Aptitude Practice",   "desc": "Quantitative aptitude, verbal, and logical reasoning practice for Cognizant assessment rounds.",             "url": "https://www.indiabix.com/",                                      "icon": "bi-calculator-fill"},
            {"site": "InterviewBit",  "label": "Cognizant Interview Prep",      "desc": "Real interview Q&A and mock rounds specifically tailored for Cognizant placement preparation.",               "url": "https://www.interviewbit.com/cognizant-interview-questions/",    "icon": "bi-chat-left-dots-fill"},
        ],
    },
    {
        "key": "capgemini",
        "name": "Capgemini",
        "color": "#0070AD",
        "description": "Aptitude, pseudocode, essay writing, and behavioral questions for Capgemini recruitment assessments.",
        "total_questions": 4,
        "resources": [
            {"site": "PrepInsta",     "label": "Capgemini Placement Papers",    "desc": "Capgemini mock tests covering aptitude, pseudocode, essay writing, and behavioral assessment rounds.",        "url": "https://prepinsta.com/capgemini/",                               "icon": "bi-file-earmark-text-fill"},
            {"site": "GeeksForGeeks", "label": "Capgemini Interview Questions", "desc": "Interview preparation guide, HR round Q&A, and technical experiences for Capgemini placements.",             "url": "https://www.geeksforgeeks.org/capgemini-interview-experience/",  "icon": "bi-mortarboard-fill"},
            {"site": "IndiaBix",      "label": "Capgemini Aptitude Practice",   "desc": "Aptitude, logical reasoning, and verbal practice sets matching Capgemini assessment patterns.",              "url": "https://www.indiabix.com/",                                      "icon": "bi-calculator-fill"},
            {"site": "InterviewBit",  "label": "Capgemini Interview Prep",      "desc": "Real Capgemini interview Q&A, placement tips, and structured mock preparation resources.",                   "url": "https://www.interviewbit.com/capgemini-interview-questions/",    "icon": "bi-chat-left-dots-fill"},
        ],
    },
]

COMPANY_HUB_MAP = {c["key"]: c for c in COMPANY_HUB}


@resources_bp.route("/company-questions")
def company_questions_home():
    if "user_id" not in session:
        return redirect("/login")
    return redirect("/tech-questions")


@resources_bp.route("/company-questions/<company_key>")
def company_questions_detail(company_key):
    if "user_id" not in session:
        return redirect("/login")
    return redirect(f"/tech-questions/{company_key}")


@resources_bp.route("/tech-questions")
def tech_questions():
    if "user_id" not in session:
        return redirect("/login")
    companies = [
        {"key": c["key"], "name": c["name"], "color": c["color"],
         "description": c["description"], "total_questions": c["total_questions"]}
        for c in COMPANY_HUB
    ]
    return render_template("tech_questions.html", companies=companies)


@resources_bp.route("/tech-questions/<company_key>")
def tech_questions_detail(company_key):
    if "user_id" not in session:
        return redirect("/login")
    company = COMPANY_HUB_MAP.get(company_key.lower())
    if not company:
        return redirect("/tech-questions")
    return render_template("company_questions.html", company=company, company_key=company_key.lower())
