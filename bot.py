import asyncio
import os
import json
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def ask_ai(system: str, user: str, history: list = []) -> str:
    messages = [{"role": "system", "content": system}]
    messages += history
    messages.append({"role": "user", "content": user})
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.1-8b-instant", "messages": messages, "max_tokens": 1500},
        timeout=60,
    )
    return resp.json()["choices"][0]["message"]["content"]

class Form(StatesGroup):
    tutor_chat   = State()
    test_waiting = State()
    test_count   = State()
    quiz_subject = State()
    quiz_active  = State()
    konspekt     = State()
    flashcard    = State()
    tarjima      = State()
    formula      = State()

SYS = {
    "tutor": "Siz Ziyrak — O'zbek tilida javob beruvchi aqlli o'quv yordamchisisiz. Savollarga aniq, sodda va tushunarli tarzda javob bering. Murakkab mavzularni oddiy misollar bilan tushuntiring.",
    "test": 'Siz test yaratuvchi botasiz. FAQAT JSON formatida javob bering, hech qanday qoshimcha matn yoq.\n{"questions":[{"q":"savol","a":["A","B","C","D"],"correct":0}]}\ncorrect — togri javob indeksi (0-3). Savollar ozbek tilida.',
    "quiz": 'Siz quiz otkazuvchi botasiz. FAQAT JSON formatida bitta savol bering:\n{"q":"savol","a":["A","B","C","D"],"correct":0,"explain":"qisqa tushuntirish"}',
    "konspekt": "Siz konspekt yaratuvchi botasiz. Katta matnni qisqacha konspektga aylantiring.\nFormat:\n📌 ASOSIY MAVZU\n\n🔑 MUHIM NUQTALAR\n• nuqta\n\n💡 XULOSA",
    "flashcard": 'Siz flashcard yaratuvchi botasiz. FAQAT JSON formatida javob bering:\n{"cards":[{"front":"savol","back":"javob"}]}\n6 ta karta yarating.',
    "tarjima": "Siz tarjimon botasiz. Ozbek, ingliz va rus tillarida tarjima qiling. Tarjima, mazni va misol jumlalar bering.",
    "formula": "Siz formula yordamchisi botasiz. Matematika, fizika va kimyo formulalarini tushuntiring. Formula, belgilar izohi, misol keltiring. Ozbek tilida.",
}

def main_menu():
    kb = InlineKeyboardBuilder()
    for text, data in [("🧠 AI Tutor","mode_tutor"),("📝 Test Generator","mode_test"),("🎯 Quiz Mode","mode_quiz"),("📋 Konspekt","mode_konspekt"),("🃏 Flashcard","mode_flashcard"),("🌐 Tarjima","mode_tarjima"),("⚗️ Formulalar","mode_formula")]:
        kb.button(text=text, callback_data=data)
    kb.adjust(2)
    return kb.as_markup()

def back_btn():
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Bosh menyu", callback_data="menu")
    return kb.as_markup()

@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("🎓 *Ziyrak Study Bot*ga xush kelibsiz!\n\nBo'lim tanlang:", reply_markup=main_menu(), parse_mode="Markdown")

@dp.message(Command("menu"))
async def cmd_menu(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("🎓 Bo'lim tanlang:", reply_markup=main_menu())

@dp.callback_query(F.data == "menu")
async def go_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("🎓 *Ziyrak Study Bot*\n\nBo'lim tanlang:", reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "mode_tutor")
async def tutor_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.tutor_chat)
    await state.update_data(history=[])
    await cb.message.edit_text("🧠 *AI Tutor*\n\nIstalgan fan bo'yicha savol bering!\n\nChiqish: /menu", reply_markup=back_btn(), parse_mode="Markdown")

@dp.message(Form.tutor_chat)
async def tutor_answer(msg: Message, state: FSMContext):
    data = await state.get_data()
    history = data.get("history", [])
    thinking = await msg.answer("💭 O'ylanmoqda...")
    try:
        reply = ask_ai(SYS["tutor"], msg.text, history[-8:])
        history.append({"role": "user", "content": msg.text})
        history.append({"role": "assistant", "content": reply})
        await state.update_data(history=history)
        await thinking.delete()
        await msg.answer(reply, reply_markup=back_btn())
    except Exception as e:
        await thinking.edit_text(f"Xatolik: {e}")

@dp.callback_query(F.data == "mode_test")
async def test_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.test_waiting)
    await cb.message.edit_text("📝 *Test Generator*\n\nMatn yuboring — test yarataman!", reply_markup=back_btn(), parse_mode="Markdown")

@dp.message(Form.test_waiting)
async def test_got_text(msg: Message, state: FSMContext):
    await state.update_data(test_text=msg.text)
    await state.set_state(Form.test_count)
    kb = InlineKeyboardBuilder()
    for n in [5, 10, 20]:
        kb.button(text=f"{n} ta savol", callback_data=f"testcount_{n}")
    kb.adjust(3)
    await msg.answer("Nechta savol?", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("testcount_"))
async def test_generate(cb: CallbackQuery, state: FSMContext):
    n = int(cb.data.split("_")[1])
    data = await state.get_data()
    await cb.message.edit_text(f"⏳ {n} ta savol yaratilmoqda...")
    try:
        raw = ask_ai(SYS["test"], f"{data['test_text']}\n\n{n} ta test savoli yarating.")
        clean = raw.strip().strip("```json").strip("```").strip()
        questions = json.loads(clean)["questions"]
        await state.update_data(questions=questions, q_idx=0, score=0, answers=[])
        await state.set_state(Form.quiz_active)
        await send_test_question(cb.message, state, questions, 0)
    except Exception as e:
        await cb.message.edit_text(f"Xatolik: {e}", reply_markup=back_btn())

async def send_test_question(msg, state, questions, idx):
    if idx >= len(questions):
        data = await state.get_data()
        score = data.get("score", 0)
        total = len(questions)
        pct = round(score/total*100)
        emoji = "🏆" if pct >= 80 else "👍" if pct >= 50 else "📚"
        text = f"{emoji} *Test yakunlandi!*\n\n✅ {score}/{total} ({pct}%)\n\n"
        answers = data.get("answers", [])
        for i, q in enumerate(questions):
            ua = answers[i] if i < len(answers) else -1
            ok = ua == q["correct"]
            text += f"{'✅' if ok else '❌'} {i+1}. {q['q']}\n"
            if not ok:
                text += f"   To'g'ri: {q['a'][q['correct']]}\n"
            text += "\n"
        await state.clear()
        await msg.answer(text[:4000], reply_markup=back_btn(), parse_mode="Markdown")
        return
    q = questions[idx]
    kb = InlineKeyboardBuilder()
    for j, opt in enumerate(q["a"]):
        kb.button(text=f"{['A','B','C','D'][j]}. {opt}", callback_data=f"testans_{j}")
    kb.adjust(1)
    await msg.answer(f"*Savol {idx+1}/{len(questions)}*\n\n{q['q']}", reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("testans_"))
async def test_answer(cb: CallbackQuery, state: FSMContext):
    j = int(cb.data.split("_")[1])
    data = await state.get_data()
    questions = data.get("questions", [])
    idx = data.get("q_idx", 0)
    score = data.get("score", 0)
    answers = data.get("answers", [])
    q = questions[idx]
    answers.append(j)
    if j == q["correct"]:
        score += 1
        await cb.answer("✅ To'g'ri!")
    else:
        await cb.answer(f"❌ To'g'risi: {q['a'][q['correct']]}")
    await state.update_data(q_idx=idx+1, score=score, answers=answers)
    await cb.message.delete()
    await send_test_question(cb.message, state, questions, idx+1)

@dp.callback_query(F.data == "mode_quiz")
async def quiz_start(cb: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    for s in ["Matematika","Fizika","Kimyo","Biologiya","Tarix","Ingliz tili"]:
        kb.button(text=s, callback_data=f"quizsub_{s}")
    kb.adjust(2)
    kb.button(text="🏠 Bosh menyu", callback_data="menu")
    await cb.message.edit_text("🎯 *Quiz Mode*\n\nFan tanlang:", reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("quizsub_"))
async def quiz_subject_chosen(cb: CallbackQuery, state: FSMContext):
    subject = cb.data.split("_", 1)[1]
    await state.update_data(quiz_subject=subject, quiz_score=0, quiz_total=0)
    await state.set_state(Form.quiz_active)
    await cb.answer()
    await send_quiz_question(cb.message, state, subject)

async def send_quiz_question(msg, state, subject):
    data = await state.get_data()
    score = data.get("quiz_score", 0)
    total = data.get("quiz_total", 0)
    wait = await msg.answer("⏳ Savol tayyorlanmoqda...")
    try:
        raw = ask_ai(SYS["quiz"], f"{subject} fanidan savol bering")
        clean = raw.strip().strip("```json").strip("```").strip()
        q = json.loads(clean)
        await state.update_data(quiz_q=q)
        kb = InlineKeyboardBuilder()
        for j, opt in enumerate(q["a"]):
            kb.button(text=f"{['A','B','C','D'][j]}. {opt}", callback_data=f"quizans_{j}")
        kb.adjust(1)
        kb.button(text="🛑 Tugatish", callback_data="quiz_end")
        await wait.delete()
        await msg.answer(f"🎯 *{subject}* | Bal: {score}/{total}\n\n{q['q']}", reply_markup=kb.as_markup(), parse_mode="Markdown")
    except Exception as e:
        await wait.edit_text(f"Xatolik: {e}", reply_markup=back_btn())

@dp.callback_query(F.data.startswith("quizans_"))
async def quiz_answer(cb: CallbackQuery, state: FSMContext):
    j = int(cb.data.split("_")[1])
    data = await state.get_data()
    q = data.get("quiz_q", {})
    score = data.get("quiz_score", 0)
    total = data.get("quiz_total", 0) + 1
    correct = q.get("correct", 0)
    if j == correct:
        score += 1
        await cb.answer("✅ To'g'ri! +1 ball")
    else:
        await cb.answer(f"❌ To'g'risi: {q['a'][correct]}")
    kb = InlineKeyboardBuilder()
    kb.button(text="➡️ Keyingi", callback_data="quiz_next")
    kb.button(text="🛑 Tugatish", callback_data="quiz_end")
    kb.adjust(2)
    await cb.message.edit_text(
        f"{'✅' if j==correct else '❌'} {q['q']}\n\nTo'g'ri: *{q['a'][correct]}*\n\n💡 {q.get('explain','')}",
        reply_markup=kb.as_markup(), parse_mode="Markdown"
    )
    await state.update_data(quiz_score=score, quiz_total=total)

@dp.callback_query(F.data == "quiz_next")
async def quiz_next(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await cb.message.delete()
    await send_quiz_question(cb.message, state, data.get("quiz_subject", "Fan"))

@dp.callback_query(F.data == "quiz_end")
async def quiz_end(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    score = data.get("quiz_score", 0)
    total = data.get("quiz_total", 0)
    pct = round(score/total*100) if total else 0
    await cb.message.edit_text(f"🏁 *Quiz yakunlandi!*\n\n🏆 {score}/{total} ({pct}%)", reply_markup=back_btn(), parse_mode="Markdown")
    await state.clear()

@dp.callback_query(F.data == "mode_konspekt")
async def konspekt_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.konspekt)
    await cb.message.edit_text("📋 *Konspekt*\n\nKatta matn yuboring!", reply_markup=back_btn(), parse_mode="Markdown")

@dp.message(Form.konspekt)
async def konspekt_make(msg: Message, state: FSMContext):
    wait = await msg.answer("⏳ Yaratilmoqda...")
    try:
        result = ask_ai(SYS["konspekt"], msg.text)
        await wait.delete()
        await msg.answer(result, reply_markup=back_btn())
    except Exception as e:
        await wait.edit_text(f"Xatolik: {e}")

@dp.callback_query(F.data == "mode_flashcard")
async def flashcard_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.flashcard)
    await cb.message.edit_text("🃏 *Flashcard*\n\nMavzu yoki matn yuboring!", reply_markup=back_btn(), parse_mode="Markdown")

@dp.message(Form.flashcard)
async def flashcard_make(msg: Message, state: FSMContext):
    wait = await msg.answer("⏳ Kartalar yaratilmoqda...")
    try:
        raw = ask_ai(SYS["flashcard"], msg.text)
        clean = raw.strip().strip("```json").strip("```").strip()
        cards = json.loads(clean)["cards"]
        await wait.delete()
        await state.update_data(cards=cards, card_idx=0)
        await send_flashcard(msg, state)
    except Exception as e:
        await wait.edit_text(f"Xatolik: {e}")

async def send_flashcard(msg, state):
    data = await state.get_data()
    cards = data.get("cards", [])
    idx = data.get("card_idx", 0)
    if idx >= len(cards):
        await msg.answer("🎉 Barcha kartalar tugadi!", reply_markup=back_btn())
        await state.clear()
        return
    card = cards[idx]
    kb = InlineKeyboardBuilder()
    kb.button(text="👁 Javobni ko'rish", callback_data="card_flip")
    await msg.answer(f"🃏 *{idx+1}/{len(cards)}*\n\n❓ {card['front']}", reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "card_flip")
async def card_flip(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cards = data.get("cards", [])
    idx = data.get("card_idx", 0)
    card = cards[idx]
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Bildim", callback_data="card_knew")
    kb.button(text="❌ Bilmadim", callback_data="card_next")
    kb.adjust(2)
    await cb.message.edit_text(f"🃏 *{idx+1}/{len(cards)}*\n\n❓ {card['front']}\n\n✅ {card['back']}", reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.in_({"card_knew", "card_next"}))
async def card_next(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(card_idx=data.get("card_idx", 0) + 1)
    await cb.message.delete()
    await send_flashcard(cb.message, state)

@dp.callback_query(F.data == "mode_tarjima")
async def tarjima_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.tarjima)
    await cb.message.edit_text("🌐 *Tarjima*\n\nSo'z yoki matn yuboring.\nUZ ↔ EN ↔ RU", reply_markup=back_btn(), parse_mode="Markdown")

@dp.message(Form.tarjima)
async def tarjima_do(msg: Message, state: FSMContext):
    wait = await msg.answer("⏳ Tarjima qilinmoqda...")
    try:
        result = ask_ai(SYS["tarjima"], msg.text)
        await wait.delete()
        await msg.answer(result, reply_markup=back_btn())
    except Exception as e:
        await wait.edit_text(f"Xatolik: {e}")

@dp.callback_query(F.data == "mode_formula")
async def formula_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.formula)
    kb = InlineKeyboardBuilder()
    for q in ["Pifagor teoremasi","F=ma","E=mc²","Ohm qonuni","Kvadrat tenglama"]:
        kb.button(text=q, callback_data=f"fml_{q}")
    kb.adjust(2)
    kb.button(text="🏠 Bosh menyu", callback_data="menu")
    await cb.message.edit_text("⚗️ *Formulalar*\n\nFormula yoki mavzu yuboring:", reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("fml_"))
async def formula_quick(cb: CallbackQuery, state: FSMContext):
    topic = cb.data.split("_", 1)[1]
    await cb.message.edit_text(f"⏳ {topic} tayyorlanmoqda...")
    try:
        result = ask_ai(SYS["formula"], topic)
        await cb.message.edit_text(result, reply_markup=back_btn())
    except Exception as e:
        await cb.message.edit_text(f"Xatolik: {e}", reply_markup=back_btn())

@dp.message(Form.formula)
async def formula_ask(msg: Message, state: FSMContext):
    wait = await msg.answer("⏳ Tayyorlanmoqda...")
    try:
        result = ask_ai(SYS["formula"], msg.text)
        await wait.delete()
        await msg.answer(result, reply_markup=back_btn())
    except Exception as e:
        await wait.edit_text(f"Xatolik: {e}")

async def main():
    print("🤖 Ziyrak Study Bot (Groq) ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
        
