#!/usr/bin/env python3
"""
Script to add sample exercises in different languages to the database.
This demonstrates how to scale the exercise database with multiple languages.
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

def add_multilingual_exercises():
    """Add sample exercises in different languages"""
    
    # Connect to database
    conn = sqlite3.connect('exercises.db')
    cursor = conn.cursor()
    
    # Sample exercises in different languages
    exercises = [
        # Spanish exercises
        {
            'title': 'El Cerebro Humano y la Plasticidad Neural',
            'text': 'El cerebro humano contiene aproximadamente 86 mil millones de neuronas, cada una capaz de formar miles de conexiones con otras neuronas. Esto crea una red compleja que procesa información a velocidades increíbles. La plasticidad neural, la capacidad del cerebro para reorganizarse, nos permite aprender nuevas habilidades a lo largo de nuestras vidas.',
            'language': 'es',
            'difficulty': 'intermediate',
            'topic': 'science',
            'questions': json.dumps([
                {
                    "question": "¿Cuántas neuronas contiene aproximadamente el cerebro humano?",
                    "options": {
                        "A": "86 millones",
                        "B": "86 mil millones",
                        "C": "860 mil millones",
                        "D": "8.6 mil millones"
                    },
                    "answer": "B"
                },
                {
                    "question": "¿Qué es la plasticidad neural?",
                    "options": {
                        "A": "La capacidad del cerebro para reorganizarse",
                        "B": "La velocidad de las conexiones neuronales",
                        "C": "El número de neuronas en el cerebro",
                        "D": "El poder de procesamiento del cerebro"
                    },
                    "answer": "A"
                }
            ])
        },
        
        # French exercises
        {
            'title': 'Le Changement Climatique et son Impact',
            'text': 'Le changement climatique est l\'un des défis les plus pressants de notre époque, affectant les écosystèmes, les modèles météorologiques et les sociétés humaines dans le monde entier. La hausse des températures mondiales entraîne la fonte des calottes glaciaires, l\'élévation du niveau de la mer et des événements météorologiques extrêmes plus fréquents.',
            'language': 'fr',
            'difficulty': 'intermediate',
            'topic': 'environment',
            'questions': json.dumps([
                {
                    "question": "Qu\'est-ce qui est identifié comme le principal moteur du changement climatique actuel?",
                    "options": {
                        "A": "Les cycles météorologiques naturels",
                        "B": "Les changements de rayonnement solaire",
                        "C": "Les activités humaines, en particulier la combustion de combustibles fossiles",
                        "D": "L\'activité volcanique"
                    },
                    "answer": "C"
                },
                {
                    "question": "Lequel des éléments suivants n\'est PAS mentionné comme conséquence de la hausse des températures mondiales?",
                    "options": {
                        "A": "La fonte des calottes glaciaires",
                        "B": "L\'élévation du niveau de la mer",
                        "C": "Des événements météorologiques extrêmes plus fréquents",
                        "D": "Des précipitations accrues partout"
                    },
                    "answer": "D"
                }
            ])
        },
        
        # German exercises
        {
            'title': 'Meereswasser und Elektrorezeption',
            'text': 'Wenn Sie Ihre Augen im Meerwasser öffnen, ist es schwierig, viel mehr als eine trübe, verschwommene grüne Farbe zu sehen. Auch Geräusche sind unverständlich und schwer zu verstehen. Ohne spezialisierte Ausrüstung wären Menschen in diesen Tiefseehabitaten verloren. Wie schaffen es Fische, es so einfach erscheinen zu lassen?',
            'language': 'de',
            'difficulty': 'advanced',
            'topic': 'science',
            'questions': json.dumps([
                {
                    "question": "Was ist das Hauptphänomen, das es Fischen ermöglicht, in Tiefseehabitaten zu navigieren?",
                    "options": {
                        "A": "Echolokation",
                        "B": "Elektrorezeption",
                        "C": "Biolumineszenz",
                        "D": "Magnetisches Empfinden"
                    },
                    "answer": "B"
                },
                {
                    "question": "Warum kommt Elektrorezeption nur bei aquatischen oder amphibischen Arten vor?",
                    "options": {
                        "A": "Weil sie in der Dunkelheit jagen müssen",
                        "B": "Weil Wasser ein effizienter Stromleiter ist",
                        "C": "Weil sie spezialisierte Gehirnstrukturen haben",
                        "D": "Weil sie sich aus Landtieren entwickelt haben"
                    },
                    "answer": "B"
                }
            ])
        },
        
        # Portuguese exercises
        {
            'title': 'Leitura e Desenvolvimento Cognitivo',
            'text': 'A leitura regular tem sido associada a vários benefícios cognitivos ao longo da vida. Estudos mostram que pessoas que leem frequentemente têm melhor memória, maior vocabulário e habilidades de pensamento crítico mais desenvolvidas. A leitura também pode ajudar a reduzir o estresse e melhorar a concentração.',
            'language': 'pt',
            'difficulty': 'beginner',
            'topic': 'education',
            'questions': json.dumps([
                {
                    "question": "Qual dos seguintes benefícios NÃO é mencionado em relação à leitura regular?",
                    "options": {
                        "A": "Melhor memória",
                        "B": "Maior vocabulário",
                        "C": "Habilidades de pensamento crítico",
                        "D": "Melhor condicionamento físico"
                    },
                    "answer": "D"
                },
                {
                    "question": "Além dos benefícios cognitivos, que outro benefício a leitura pode proporcionar?",
                    "options": {
                        "A": "Aumentar a altura",
                        "B": "Reduzir o estresse",
                        "C": "Melhorar a visão",
                        "D": "Aumentar a velocidade"
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
    cursor.execute("SELECT language, COUNT(*) FROM exercises GROUP BY language")
    stats = cursor.fetchall()
    
    print("\n📊 Database Statistics:")
    for lang, count in stats:
        print(f"  {lang.upper()}: {count} exercises")
    
    cursor.execute("SELECT COUNT(*) FROM exercises")
    total = cursor.fetchone()[0]
    print(f"\n📚 Total exercises: {total}")
    
    conn.close()

if __name__ == "__main__":
    print("🌍 Adding multilingual exercises to database...")
    print("📊 Initializing database...")
    init_database()
    add_multilingual_exercises()
    print("\n✅ Done! You can now filter exercises by language using the API:")
    print("   GET /exercises?language=es  (Spanish)")
    print("   GET /exercises?language=fr  (French)")
    print("   GET /exercises?language=de  (German)")
    print("   GET /exercises?language=pt  (Portuguese)")
    print("   GET /exercises?language=en  (English)")
