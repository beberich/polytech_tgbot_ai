from neo4j import GraphDatabase
from docx import Document
from secret_info import AUTH

URI = "bolt+ssc://69a59345.databases.neo4j.io"

example_name = ['bolt+ssc', 'bolt+s', 'neo4j+ssc', 'neo4j+s']

driver = GraphDatabase.driver(URI, auth=AUTH)


def create_topic(tx, topic_name):
    query = "MERGE (t:Topic {name: $name}) RETURN elementId(t)"
    result = tx.run(query, name=topic_name).single()
    return result[0] if result else None


def create_subtopic(tx, subtopic_name, topic_id):
    if topic_id is None:
        print(f"Ошибка: topic_id = None для {subtopic_name}")
        return None

    query = """
    MATCH (t) WHERE elementId(t) = $topic_id
    MERGE (s:Subtopic {name: $name})
    MERGE (t)-[:HAS_SUBTOPIC]->(s)
    RETURN elementId(s)
    """
    result = tx.run(query, name=subtopic_name, topic_id=topic_id).single()
    return result[0] if result else None


def create_chunk(tx, chunk_text, subtopic_id):
    query = """
    MATCH (s) WHERE elementId(s) = $subtopic_id
    CREATE (c:Chunk {text: $text})
    CREATE (s)-[:HAS_CHUNK]->(c)
    """
    tx.run(query, text=chunk_text, subtopic_id=subtopic_id)


def parse_document(file_path):
    doc = Document(file_path)
    topics = {}
    current_topic = None
    current_subtopic = None

    for para in doc.paragraphs:
        text = para.text.strip()
        if text.isdigit() or text == "":
            continue
        if text.endswith("?"):
            current_subtopic = text
            topics[current_topic][current_subtopic] = []
        elif text.startswith(tuple(str(i) for i in range(1, 11))):
            current_topic = text
            topics[current_topic] = {}
        elif current_subtopic:
            if current_topic not in topics:
                topics[current_topic] = {}

            if current_subtopic not in topics[current_topic]:
                topics[current_topic][current_subtopic] = []

            topics[current_topic][current_subtopic].append(text)

    return topics


def load_to_neo4j(data):
    with driver.session() as session:
        for topic, subtopics in data.items():
            topic_id = session.execute_write(create_topic, topic)
            print(f"Создан topic_id: {topic_id}")  # Проверка
            if topic_id is None:
                continue  # Пропустить, если топик не создался

            for subtopic, chunks in subtopics.items():
                subtopic_id = session.execute_write(create_subtopic, subtopic, topic_id)
                print(f"Создан subtopic_id: {subtopic_id}")  # Проверка
                if subtopic_id is None:
                    continue  # Пропустить, если подтема не создалась

                for chunk in chunks:
                    session.execute_write(create_chunk, chunk, subtopic_id)


if __name__ == "__main__":
    file_path = "Вопросы_парсинг.docx"
    parsed_data = parse_document(file_path)
    load_to_neo4j(parsed_data)
    driver.close()
