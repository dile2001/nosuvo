#!/usr/bin/env python3
"""
Script to add Vietnamese, Japanese, and Chinese exercises to the database.
"""

import sqlite3
import json

def init_database():
    """Initialize the SQLite database with exercises table"""
    conn = sqlite3.connect('exercises.db')
    cursor = conn.cursor()
    
    # Create exercises table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            difficulty TEXT DEFAULT 'intermediate',
            topic TEXT DEFAULT 'general',
            questions TEXT NOT NULL,  -- JSON string of questions
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_language ON exercises(language)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_difficulty ON exercises(difficulty)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_topic ON exercises(topic)')
    
    conn.commit()
    conn.close()

def add_asian_language_exercises():
    """Add Vietnamese, Japanese, and Chinese exercises"""
    
    # Connect to database
    conn = sqlite3.connect('exercises.db')
    cursor = conn.cursor()
    
    # Sample exercises in Asian languages
    exercises = [
        # Vietnamese exercises
        {
            'title': 'Trí Tuệ Nhân Tạo và Tương Lai',
            'text': 'Trí tuệ nhân tạo đang thay đổi cách chúng ta sống và làm việc. Từ việc lái xe tự động đến chẩn đoán y tế, AI đang trở thành một phần không thể thiếu trong cuộc sống hiện đại. Tuy nhiên, sự phát triển nhanh chóng của AI cũng đặt ra nhiều câu hỏi về đạo đức và tác động xã hội. Chúng ta cần cân nhắc cẩn thận về cách sử dụng công nghệ này một cách có trách nhiệm.',
            'language': 'vi',
            'difficulty': 'intermediate',
            'topic': 'technology',
            'questions': json.dumps([
                {
                    "question": "Trí tuệ nhân tạo đang thay đổi điều gì?",
                    "options": {
                        "A": "Cách chúng ta ăn uống",
                        "B": "Cách chúng ta sống và làm việc",
                        "C": "Cách chúng ta ngủ",
                        "D": "Cách chúng ta tập thể thao"
                    },
                    "answer": "B"
                },
                {
                    "question": "AI được sử dụng trong lĩnh vực nào?",
                    "options": {
                        "A": "Chỉ trong giải trí",
                        "B": "Lái xe tự động và chẩn đoán y tế",
                        "C": "Chỉ trong giáo dục",
                        "D": "Chỉ trong nông nghiệp"
                    },
                    "answer": "B"
                },
                {
                    "question": "Sự phát triển của AI đặt ra vấn đề gì?",
                    "options": {
                        "A": "Vấn đề về màu sắc",
                        "B": "Câu hỏi về đạo đức và tác động xã hội",
                        "C": "Vấn đề về âm nhạc",
                        "D": "Vấn đề về thời trang"
                    },
                    "answer": "B"
                }
            ])
        },
        
        # Japanese exercises
        {
            'title': '日本の伝統文化と現代社会',
            'text': '日本は豊かな伝統文化を持つ国です。茶道、華道、書道などの伝統芸術は、日本人の精神性と美意識を表しています。しかし、現代のグローバル化社会において、これらの伝統文化は新しい意味と価値を持っています。多くの外国人観光客が日本の文化に興味を持ち、伝統的な体験を求めています。これは文化の国際交流と理解を深める良い機会でもあります。',
            'language': 'ja',
            'difficulty': 'intermediate',
            'topic': 'culture',
            'questions': json.dumps([
                {
                    "question": "日本の伝統芸術にはどのようなものがありますか？",
                    "options": {
                        "A": "茶道、華道、書道",
                        "B": "サッカー、野球、テニス",
                        "C": "料理、掃除、洗濯",
                        "D": "映画、音楽、ダンス"
                    },
                    "answer": "A"
                },
                {
                    "question": "現代社会で伝統文化はどのような意味を持っていますか？",
                    "options": {
                        "A": "古いものとして忘れられている",
                        "B": "新しい意味と価値を持っている",
                        "C": "全く関係がない",
                        "D": "邪魔になっている"
                    },
                    "answer": "B"
                },
                {
                    "question": "外国人観光客の増加は何をもたらしていますか？",
                    "options": {
                        "A": "問題だけを生み出している",
                        "B": "文化の国際交流と理解を深める機会",
                        "C": "伝統文化を破壊している",
                        "D": "何の影響もない"
                    },
                    "answer": "B"
                }
            ])
        },
        
        # Chinese exercises (Simplified)
        {
            'title': '可持续发展与环境保护',
            'text': '可持续发展是当今世界面临的重要挑战。随着全球人口的增长和经济的发展，我们对自然资源的需求不断增加。气候变化、空气污染、水资源短缺等问题日益严重。为了实现可持续发展，我们需要采用清洁能源，减少废物产生，保护生物多样性。每个人都可以通过改变生活方式来为环境保护做出贡献，比如节约用水、使用公共交通、减少塑料使用等。',
            'language': 'zh',
            'difficulty': 'intermediate',
            'topic': 'environment',
            'questions': json.dumps([
                {
                    "question": "可持续发展面临的主要挑战是什么？",
                    "options": {
                        "A": "人口增长和经济发展",
                        "B": "科技进步",
                        "C": "教育改革",
                        "D": "艺术发展"
                    },
                    "answer": "A"
                },
                {
                    "question": "以下哪个不是环境问题？",
                    "options": {
                        "A": "气候变化",
                        "B": "空气污染",
                        "C": "水资源短缺",
                        "D": "网络速度"
                    },
                    "answer": "D"
                },
                {
                    "question": "个人如何为环境保护做贡献？",
                    "options": {
                        "A": "使用更多塑料制品",
                        "B": "节约用水、使用公共交通、减少塑料使用",
                        "C": "增加汽车使用",
                        "D": "浪费更多资源"
                    },
                    "answer": "B"
                }
            ])
        },
        
        # Chinese exercises (Traditional)
        {
            'title': '科技創新與未來發展',
            'text': '科技創新是推動社會進步的重要動力。從互聯網到人工智能，從新能源到生物技術，科技創新正在改變我們的生活方式和工作模式。然而，科技發展也帶來了新的挑戰，如數據隱私、就業結構變化等問題。我們需要在享受科技帶來便利的同時，也要思考如何應對這些挑戰，確保科技發展能夠造福全人類。',
            'language': 'zh-tw',
            'difficulty': 'advanced',
            'topic': 'technology',
            'questions': json.dumps([
                {
                    "question": "科技創新的作用是什麼？",
                    "options": {
                        "A": "推動社會進步",
                        "B": "增加工作負擔",
                        "C": "減少娛樂活動",
                        "D": "降低生活質量"
                    },
                    "answer": "A"
                },
                {
                    "question": "科技發展帶來了哪些挑戰？",
                    "options": {
                        "A": "數據隱私、就業結構變化",
                        "B": "天氣變化",
                        "C": "食物短缺",
                        "D": "交通堵塞"
                    },
                    "answer": "A"
                },
                {
                    "question": "我們應該如何應對科技發展的挑戰？",
                    "options": {
                        "A": "停止科技發展",
                        "B": "思考如何應對挑戰，確保科技發展造福全人類",
                        "C": "忽視這些挑戰",
                        "D": "只關注科技發展"
                    },
                    "answer": "B"
                }
            ])
        }
    ]
    
    # Insert exercises
    for exercise in exercises:
        try:
            cursor.execute('''
                INSERT INTO exercises (title, text, language, difficulty, topic, questions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                exercise['title'],
                exercise['text'],
                exercise['language'],
                exercise['difficulty'],
                exercise['topic'],
                exercise['questions']
            ))
            print(f"✅ Added {exercise['language']} exercise: {exercise['title']}")
        except Exception as e:
            print(f"❌ Error adding {exercise['title']}: {e}")
    
    # Commit changes
    conn.commit()
    
    # Show statistics
    cursor.execute("SELECT language, COUNT(*) FROM exercises GROUP BY language ORDER BY language")
    stats = cursor.fetchall()
    
    print("\n📊 Database Statistics:")
    for lang, count in stats:
        language_names = {
            'de': 'German',
            'en': 'English', 
            'es': 'Spanish',
            'fr': 'French',
            'ja': 'Japanese',
            'pt': 'Portuguese',
            'vi': 'Vietnamese',
            'zh': 'Chinese (Simplified)',
            'zh-tw': 'Chinese (Traditional)'
        }
        lang_name = language_names.get(lang, lang.upper())
        print(f"  {lang_name}: {count} exercises")
    
    cursor.execute("SELECT COUNT(*) FROM exercises")
    total = cursor.fetchone()[0]
    print(f"\n📚 Total exercises: {total}")
    
    conn.close()

if __name__ == "__main__":
    print("🌏 Adding Vietnamese, Japanese, and Chinese exercises to database...")
    print("📊 Initializing database...")
    init_database()
    add_asian_language_exercises()
    print("\n✅ Done! You can now filter exercises by language using the API:")
    print("   GET /exercises?language=vi      (Vietnamese)")
    print("   GET /exercises?language=ja      (Japanese)")
    print("   GET /exercises?language=zh      (Chinese Simplified)")
    print("   GET /exercises?language=zh-tw   (Chinese Traditional)")
    print("\n🌍 All supported languages:")
    print("   en, es, fr, de, pt, vi, ja, zh, zh-tw")
