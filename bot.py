import json
import torch
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from rapidfuzz import process, fuzz
import logging
from secret_tg_info import TOKEN

TELEGRAM_TOKEN = TOKEN
DATASET_PATH = "clean_structured_dataset.json"
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
LORA_ADAPTER_PATH = "trained_tinyllama"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

print("Загружаем модель")
base_model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, device_map="auto", load_in_8bit=True)
tokenizer = AutoTokenizer.from_pretrained(LORA_ADAPTER_PATH)
model = PeftModel.from_pretrained(base_model, LORA_ADAPTER_PATH)
model.eval()
print("Модель загружена.")

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

qa_pairs = []
for topic in raw_data:
    for dialog in topic.get("dialogs", []):
        user_msg, bot_msg = None, None
        for msg in dialog.get("messages", []):
            if msg["role"] == "user":
                user_msg = msg["content"].strip()
            elif msg["role"] == "assistant" and user_msg:
                bot_msg = msg["content"].strip()
                qa_pairs.append((user_msg, bot_msg))
                user_msg = None


def find_best_match(user_input, threshold=85):
    questions = [q for q, _ in qa_pairs]
    match, score, idx = process.extractOne(user_input, questions, scorer=fuzz.token_sort_ratio)
    if score >= threshold:
        return qa_pairs[idx][1]
    return None


def generate_local_answer(user_input):
    prompt = f"<|user|>\n{user_input}\n<|assistant|>\n"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=200,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id
        )
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    if "<|assistant|>" in response:
        response = response.split("<|assistant|>")[-1].strip()
    return response.strip()


@dp.message_handler()
async def handle_message(message: types.Message):
    user_input = message.text.strip()

    answer = find_best_match(user_input)
    if answer:
        await message.answer(answer)
        return

    await message.answer("Думаю над ответом...")
    try:
        response = generate_local_answer(user_input)
        await message.answer(response)
    except Exception as e:
        logging.error(f"Ошибка генерации: {e}")
        await message.answer("Ошибка при генерации ответа.")


if __name__ == "__main__":
    print("Бот запущен.")
    executor.start_polling(dp, skip_updates=True)
