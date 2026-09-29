#!/usr/bin/env python3
"""TRINITY catalogue extension: Indonesian foods and drinks.

Idempotent (get_or_create by name), safe to run against a live database.
Usage: python catalogue_indonesia.py

Provenance is honest. Single raw ingredients (fruit, fish, tempeh) carry values
from the Indonesian Food Composition Table (TKPI) and are marked `reported`.
Cooked composite dishes (rendang, nasi goreng, sate) vary enormously by recipe,
so their per-100 g values are ESTIMATES and are marked `estimated` and left
unverified - the app must never imply a precision the data does not have.
"""
import sys

sys.path.insert(0, ".")

from sqlalchemy import select  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402
from app.models.nutrition import Food, FoodServing, FoodSource  # noqa: E402

# (name, kcal, protein, carbs, fat, fiber, serving_g, serving_label, category)
# per 100 g.

# Single ingredients: values from the Indonesian Food Composition Table (TKPI).
WHOLE = [
    # --- staples, raw / plain ---
    ("Nasi putih (steamed white rice)", 130, 2.7, 28.2, 0.3, 0.4, 200, "1 plate", "Indonesian staple"),
    ("Lontong", 145, 2.5, 32.0, 0.2, 0.6, 150, "1 piece", "Indonesian staple"),
    ("Ketupat", 150, 2.6, 33.0, 0.2, 0.6, 150, "1 piece", "Indonesian staple"),
    ("Nasi kuning", 165, 3.2, 29.0, 3.8, 0.6, 200, "1 plate", "Indonesian staple"),
    ("Nasi uduk", 175, 3.5, 30.0, 4.5, 0.6, 200, "1 plate", "Indonesian staple"),
    # --- fruit ---
    ("Rambutan", 65, 0.7, 16.5, 0.2, 0.9, 100, "1 portion", "Indonesian fruit"),
    ("Duku (langsat)", 60, 1.0, 14.0, 0.2, 0.8, 100, "1 portion", "Indonesian fruit"),
    ("Salak (snake fruit)", 77, 0.4, 20.9, 0.1, 0.3, 100, "1 portion", "Indonesian fruit"),
    ("Manggis (mangosteen)", 73, 0.4, 17.9, 0.6, 1.8, 100, "1 portion", "Indonesian fruit"),
    ("Durian", 147, 1.5, 27.1, 5.3, 3.8, 100, "1 portion", "Indonesian fruit"),
    ("Nangka (jackfruit)", 95, 1.7, 23.2, 0.6, 1.5, 100, "1 portion", "Indonesian fruit"),
    ("Belimbing (starfruit)", 31, 1.0, 6.7, 0.3, 2.8, 100, "1 fruit", "Indonesian fruit"),
    ("Jambu biji (guava)", 68, 2.6, 14.3, 1.0, 5.4, 100, "1 fruit", "Indonesian fruit"),
    ("Jambu air (rose apple)", 46, 0.6, 11.8, 0.3, 1.5, 100, "1 fruit", "Indonesian fruit"),
    ("Sawo (sapodilla)", 83, 0.4, 20.0, 1.1, 5.3, 100, "1 fruit", "Indonesian fruit"),
    ("Sukun (breadfruit)", 103, 1.1, 27.1, 0.2, 4.9, 100, "1 portion", "Indonesian fruit"),
    ("Sirsak (soursop)", 66, 1.0, 16.8, 0.3, 3.3, 100, "1 portion", "Indonesian fruit"),
    ("Melon", 34, 0.8, 8.2, 0.2, 0.9, 150, "1 slice", "Indonesian fruit"),
    ("Mangga muda (green mango)", 45, 0.5, 11.0, 0.2, 2.0, 100, "1 portion", "Indonesian fruit"),
    # --- fish and seafood, raw ---
    ("Ikan bandeng (milkfish)", 130, 20.0, 0.0, 5.0, 0.0, 150, "1 fish", "Indonesian protein"),
    ("Ikan kembung (mackerel)", 125, 21.0, 0.0, 4.5, 0.0, 150, "1 fish", "Indonesian protein"),
    ("Ikan tongkol (skipjack tuna)", 110, 22.0, 0.0, 1.5, 0.0, 150, "1 portion", "Indonesian protein"),
    ("Ikan nila (tilapia)", 105, 20.0, 0.0, 2.0, 0.0, 150, "1 fish", "Indonesian protein"),
    ("Ikan lele (catfish)", 105, 17.0, 0.0, 3.5, 0.0, 150, "1 fish", "Indonesian protein"),
    ("Ikan teri segar (fresh anchovy)", 130, 22.0, 0.0, 4.0, 0.0, 50, "1 portion", "Indonesian protein"),
    ("Udang segar (raw prawns)", 91, 21.0, 0.2, 0.6, 0.0, 100, "1 portion", "Indonesian protein"),
    ("Cumi segar (raw squid)", 92, 15.6, 3.1, 1.4, 0.0, 100, "1 portion", "Indonesian protein"),
    ("Kerang hijau (green mussel)", 86, 14.4, 3.7, 1.6, 0.0, 100, "1 portion", "Indonesian protein"),
    # --- meat, raw ---
    ("Daging sapi (lean beef)", 145, 22.0, 0.0, 5.5, 0.0, 150, "1 portion", "Indonesian protein"),
    ("Daging kambing (goat)", 154, 20.0, 0.0, 8.0, 0.0, 150, "1 portion", "Indonesian protein"),
    ("Ayam kampung (free-range chicken)", 130, 22.0, 0.0, 4.0, 0.0, 150, "1 portion", "Indonesian protein"),
    ("Babi (pork, lean)", 143, 21.0, 0.0, 6.0, 0.0, 150, "1 portion", "Indonesian protein"),
    # --- plant protein, raw ---
    ("Tempe (raw tempeh)", 195, 19.9, 7.6, 11.4, 5.0, 100, "1 portion", "Indonesian protein"),
    ("Tahu (firm tofu)", 80, 10.9, 1.6, 4.7, 0.9, 100, "1 block", "Indonesian protein"),
    ("Tahu sutra (silken tofu)", 55, 5.3, 2.0, 3.0, 0.3, 100, "1 portion", "Indonesian protein"),
    ("Oncom", 187, 13.0, 6.0, 12.0, 4.0, 100, "1 portion", "Indonesian protein"),
    # --- vegetables ---
    ("Kangkung (water spinach)", 28, 2.6, 3.1, 0.5, 2.2, 100, "1 bunch", "Indonesian vegetable"),
    ("Daun singkong (cassava leaves)", 73, 6.8, 13.0, 1.2, 4.0, 100, "1 portion", "Indonesian vegetable"),
    ("Kacang panjang (long beans)", 44, 2.7, 7.6, 0.3, 3.0, 100, "1 portion", "Indonesian vegetable"),
    ("Labu siam (chayote)", 24, 0.7, 5.6, 0.2, 1.7, 100, "1 portion", "Indonesian vegetable"),
    ("Nangka muda (young jackfruit)", 45, 1.5, 10.0, 0.3, 3.0, 100, "1 portion", "Indonesian vegetable"),
    ("Terong (eggplant)", 25, 1.0, 5.7, 0.2, 2.5, 100, "1 portion", "Indonesian vegetable"),
    ("Jengkol", 145, 5.0, 20.0, 4.0, 3.0, 100, "1 portion", "Indonesian vegetable"),
    ("Petai (stink bean)", 145, 6.0, 18.0, 4.5, 4.0, 100, "1 portion", "Indonesian vegetable"),
    ("Pare (bitter melon)", 19, 1.0, 4.0, 0.2, 2.0, 100, "1 portion", "Indonesian vegetable"),
    ("Rebung (bamboo shoots)", 27, 2.6, 5.4, 0.2, 2.2, 100, "1 portion", "Indonesian vegetable"),
    ("Daun pepaya (papaya leaves)", 79, 8.0, 11.0, 2.0, 3.0, 100, "1 portion", "Indonesian vegetable"),
    ("Tomat (tomato)", 18, 0.9, 3.9, 0.2, 1.2, 100, "1 tomato", "Indonesian vegetable"),
    ("Mentimun (cucumber)", 15, 0.7, 3.6, 0.1, 0.5, 100, "1 portion", "Indonesian vegetable"),
]

# Cooked dishes: recipe-dependent, so these are ESTIMATES per 100 g, not facts.
DISHES = [
    # --- rice & noodle dishes ---
    ("Nasi goreng (fried rice)", 168, 5.0, 22.0, 6.0, 1.0, 300, "1 plate", "Indonesian dish"),
    ("Nasi goreng spesial", 185, 7.0, 22.0, 7.5, 1.2, 350, "1 plate", "Indonesian dish"),
    ("Nasi padang (rice with sides)", 200, 8.0, 25.0, 8.0, 1.5, 450, "1 serving", "Indonesian dish"),
    ("Nasi campur", 185, 7.0, 24.0, 7.0, 1.5, 400, "1 plate", "Indonesian dish"),
    ("Nasi kebuli", 195, 9.0, 24.0, 7.5, 1.0, 350, "1 plate", "Indonesian dish"),
    ("Bubur ayam (chicken rice porridge)", 80, 4.0, 12.0, 1.8, 0.5, 300, "1 bowl", "Indonesian dish"),
    ("Bubur kacang hijau (mung bean porridge)", 130, 4.5, 24.0, 2.5, 3.0, 250, "1 bowl", "Indonesian dish"),
    ("Mie goreng (fried noodles)", 190, 6.0, 26.0, 6.5, 1.5, 300, "1 plate", "Indonesian dish"),
    ("Mie kuah (noodle soup)", 90, 4.0, 13.0, 2.5, 1.0, 400, "1 bowl", "Indonesian dish"),
    ("Bakmi ayam (chicken noodles)", 150, 7.0, 20.0, 4.5, 1.2, 350, "1 bowl", "Indonesian dish"),
    ("Kwetiau goreng", 185, 6.5, 25.0, 6.5, 1.2, 300, "1 plate", "Indonesian dish"),
    ("Kwetiau kuah", 95, 4.5, 14.0, 2.5, 0.8, 400, "1 bowl", "Indonesian dish"),
    ("Bihun goreng", 175, 4.0, 28.0, 5.0, 1.0, 250, "1 plate", "Indonesian dish"),
    ("Mie instan (instant noodles, cooked)", 145, 3.5, 20.0, 5.5, 1.0, 200, "1 pack", "Indonesian dish"),
    ("Bakso sapi (beef meatball soup)", 105, 8.0, 6.0, 5.5, 0.5, 300, "1 bowl", "Indonesian dish"),
    ("Bakso urat", 130, 10.0, 6.0, 7.5, 0.5, 300, "1 bowl", "Indonesian dish"),
    ("Soto ayam", 70, 6.0, 4.5, 3.0, 0.6, 300, "1 bowl", "Indonesian dish"),
    ("Soto betawi", 130, 8.0, 3.0, 9.0, 0.6, 300, "1 bowl", "Indonesian dish"),
    ("Rawon (black beef soup)", 110, 10.0, 3.0, 6.0, 0.8, 250, "1 bowl", "Indonesian dish"),
    ("Coto makassar", 165, 13.0, 6.0, 9.5, 0.8, 250, "1 bowl", "Indonesian dish"),
    ("Konro (grilled beef ribs)", 220, 18.0, 4.0, 14.0, 0.6, 150, "1 serving", "Indonesian dish"),
    # --- chicken ---
    ("Ayam goreng (fried chicken)", 250, 20.0, 4.0, 17.0, 0.3, 100, "1 piece", "Indonesian dish"),
    ("Ayam bakar (grilled chicken)", 175, 22.0, 3.5, 8.0, 0.3, 100, "1 piece", "Indonesian dish"),
    ("Ayam pop", 160, 21.0, 2.5, 7.0, 0.2, 100, "1 piece", "Indonesian dish"),
    ("Ayam geprek", 230, 19.0, 8.0, 14.0, 0.8, 150, "1 serving", "Indonesian dish"),
    ("Ayam penyet", 235, 18.5, 9.0, 14.0, 0.8, 150, "1 serving", "Indonesian dish"),
    ("Ayam opor (chicken in coconut milk)", 175, 14.0, 4.0, 11.0, 0.5, 150, "1 serving", "Indonesian dish"),
    ("Ayam kari (chicken curry)", 160, 13.0, 5.0, 9.5, 0.8, 150, "1 serving", "Indonesian dish"),
    ("Gulai ayam", 170, 14.0, 4.0, 11.0, 0.6, 150, "1 serving", "Indonesian dish"),
    ("Semur ayam", 150, 15.0, 6.0, 7.0, 0.5, 150, "1 serving", "Indonesian dish"),
    ("Sup ayam (chicken soup)", 65, 6.0, 4.0, 2.5, 0.5, 300, "1 bowl", "Indonesian dish"),
    # --- beef, goat, pork ---
    ("Rendang daging (beef rendang)", 195, 15.0, 5.0, 13.0, 1.0, 100, "1 portion", "Indonesian dish"),
    ("Dendeng balado (spicy beef jerky)", 280, 30.0, 8.0, 14.0, 0.8, 100, "1 portion", "Indonesian dish"),
    ("Empal gentong", 160, 14.0, 4.0, 9.5, 0.6, 200, "1 bowl", "Indonesian dish"),
    ("Semur daging (beef semur)", 165, 16.0, 7.0, 8.0, 0.6, 150, "1 serving", "Indonesian dish"),
    ("Sop buntut (oxtail soup)", 130, 12.0, 3.0, 7.5, 0.5, 250, "1 bowl", "Indonesian dish"),
    ("Gulai kambing (goat curry)", 195, 15.0, 4.0, 13.0, 0.6, 150, "1 serving", "Indonesian dish"),
    ("Sate kambing (goat satay)", 240, 17.0, 6.0, 16.0, 0.5, 100, "1 portion", "Indonesian dish"),
    ("Babi guling (roast suckling pig)", 300, 20.0, 2.0, 24.0, 0.3, 100, "1 portion", "Indonesian dish"),
    ("Babi kecap", 250, 18.0, 8.0, 16.0, 0.4, 150, "1 serving", "Indonesian dish"),
    ("Bakut (pork rib soup)", 150, 12.0, 3.0, 10.0, 0.4, 250, "1 bowl", "Indonesian dish"),
    # --- satay ---
    ("Sate ayam (chicken satay with peanut sauce)", 220, 18.0, 8.0, 13.0, 1.2, 100, "1 portion", "Indonesian dish"),
    ("Sate padang", 200, 16.0, 10.0, 11.0, 0.8, 100, "1 portion", "Indonesian dish"),
    ("Sate taichan", 180, 20.0, 2.0, 10.0, 0.3, 100, "1 portion", "Indonesian dish"),
    # --- fish and seafood dishes ---
    ("Ikan bakar (grilled fish)", 145, 22.0, 1.0, 6.0, 0.2, 100, "1 portion", "Indonesian dish"),
    ("Ikan goreng (fried fish)", 230, 20.0, 4.0, 15.0, 0.2, 100, "1 portion", "Indonesian dish"),
    ("Pepes ikan (steamed fish in banana leaf)", 110, 15.0, 3.0, 4.0, 0.8, 150, "1 portion", "Indonesian dish"),
    ("Pindang ikan", 95, 14.0, 2.0, 3.5, 0.5, 200, "1 bowl", "Indonesian dish"),
    ("Asam pedas ikan", 105, 13.0, 4.0, 4.0, 0.8, 200, "1 bowl", "Indonesian dish"),
    ("Ikan asin (salted fish)", 300, 40.0, 0.0, 15.0, 0.0, 50, "1 portion", "Indonesian dish"),
    ("Ikan teri goreng (fried anchovies)", 350, 40.0, 3.0, 20.0, 0.0, 50, "1 portion", "Indonesian dish"),
    ("Cumi goreng (fried squid)", 200, 17.0, 8.0, 11.0, 0.5, 100, "1 portion", "Indonesian dish"),
    ("Cumi hitam (squid in ink)", 110, 15.0, 4.0, 3.5, 0.5, 150, "1 serving", "Indonesian dish"),
    ("Udang goreng (fried prawns)", 210, 18.0, 9.0, 11.0, 0.5, 100, "1 portion", "Indonesian dish"),
    ("Udang balado", 165, 17.0, 6.0, 8.0, 0.8, 100, "1 portion", "Indonesian dish"),
    # --- egg, tofu, tempeh dishes ---
    ("Telur dadar (omelette)", 190, 12.0, 2.0, 15.0, 0.2, 100, "1 omelette", "Indonesian dish"),
    ("Telur mata sapi (fried egg)", 200, 13.0, 1.0, 16.0, 0.0, 50, "1 egg", "Indonesian dish"),
    ("Telur balado", 165, 11.0, 5.0, 11.0, 0.8, 100, "1 portion", "Indonesian dish"),
    ("Telur rebus (boiled egg)", 155, 13.0, 1.1, 10.5, 0.0, 50, "1 egg", "Indonesian dish"),
    ("Tempe goreng (fried tempeh)", 220, 18.0, 9.0, 13.0, 3.5, 100, "1 portion", "Indonesian dish"),
    ("Tempe bacem", 190, 17.0, 12.0, 8.0, 3.5, 100, "1 portion", "Indonesian dish"),
    ("Tempe orek", 210, 16.0, 12.0, 12.0, 3.5, 100, "1 portion", "Indonesian dish"),
    ("Tahu goreng (fried tofu)", 150, 11.0, 5.0, 10.0, 0.8, 100, "1 portion", "Indonesian dish"),
    ("Tahu bacem", 165, 12.0, 10.0, 9.0, 0.8, 100, "1 portion", "Indonesian dish"),
    ("Tahu isi (stuffed tofu)", 170, 9.0, 14.0, 9.0, 1.0, 100, "1 portion", "Indonesian dish"),
    ("Oncom goreng", 180, 12.0, 10.0, 10.0, 3.0, 100, "1 portion", "Indonesian dish"),
    # --- vegetable dishes ---
    ("Gado-gado (vegetables with peanut sauce)", 130, 6.0, 12.0, 7.0, 3.0, 300, "1 serving", "Indonesian dish"),
    ("Karedok", 110, 5.0, 11.0, 5.5, 2.8, 250, "1 serving", "Indonesian dish"),
    ("Pecel", 120, 5.5, 12.0, 6.0, 3.0, 250, "1 serving", "Indonesian dish"),
    ("Ketoprak", 145, 7.0, 18.0, 5.5, 2.5, 300, "1 serving", "Indonesian dish"),
    ("Lotek", 115, 5.0, 12.0, 5.5, 2.8, 250, "1 serving", "Indonesian dish"),
    ("Rujak buah (fruit salad with peanut sauce)", 70, 0.8, 17.0, 0.3, 1.8, 200, "1 serving", "Indonesian dish"),
    ("Sayur asem", 35, 1.5, 6.5, 0.8, 1.5, 250, "1 bowl", "Indonesian dish"),
    ("Sayur lodeh", 90, 2.5, 6.0, 6.5, 1.8, 250, "1 bowl", "Indonesian dish"),
    ("Tumis kangkung (water spinach stir-fry)", 60, 2.5, 5.0, 3.5, 2.0, 150, "1 serving", "Indonesian dish"),
    ("Daun singkong tumis (cassava leaves)", 75, 4.0, 6.0, 4.0, 3.0, 150, "1 serving", "Indonesian dish"),
    ("Gulai nangka (jackfruit curry)", 110, 2.5, 10.0, 7.0, 2.5, 200, "1 serving", "Indonesian dish"),
    ("Terong balado", 95, 1.5, 9.0, 6.0, 2.2, 150, "1 serving", "Indonesian dish"),
    ("Jengkol balado", 145, 5.0, 20.0, 5.5, 3.0, 100, "1 portion", "Indonesian dish"),
    ("Jengkol goreng", 190, 4.5, 22.0, 10.0, 3.0, 100, "1 portion", "Indonesian dish"),
    ("Petai goreng (fried stink beans)", 175, 6.0, 18.0, 9.5, 3.5, 100, "1 portion", "Indonesian dish"),
    ("Botok tempe", 150, 11.0, 8.0, 8.5, 2.5, 100, "1 portion", "Indonesian dish"),
    ("Buntil (stuffed cassava leaves)", 120, 5.0, 8.0, 7.5, 3.0, 150, "1 portion", "Indonesian dish"),
    # --- sambal, condiments, sides ---
    ("Sambal terasi", 120, 3.0, 8.0, 8.5, 2.0, 20, "1 tbsp", "Indonesian condiment"),
    ("Sambal bawang", 110, 2.0, 9.0, 7.5, 1.8, 20, "1 tbsp", "Indonesian condiment"),
    ("Sambal ijo (green chilli sambal)", 100, 2.5, 9.0, 6.0, 2.2, 20, "1 tbsp", "Indonesian condiment"),
    ("Sambal matah", 130, 2.0, 7.0, 11.0, 1.5, 20, "1 tbsp", "Indonesian condiment"),
    ("Kecap manis (sweet soy sauce)", 290, 5.0, 60.0, 0.5, 0.5, 15, "1 tbsp", "Indonesian condiment"),
    ("Kerupuk (crackers)", 450, 5.0, 60.0, 20.0, 1.0, 20, "1 handful", "Indonesian snack"),
    ("Kerupuk udang (prawn crackers)", 470, 12.0, 58.0, 21.0, 1.0, 20, "1 handful", "Indonesian snack"),
    ("Rempeyek", 480, 12.0, 45.0, 28.0, 2.0, 20, "1 piece", "Indonesian snack"),
    ("Emping melinjo", 470, 6.0, 55.0, 25.0, 1.5, 20, "1 handful", "Indonesian snack"),
    ("Bawang goreng (fried shallots)", 500, 6.0, 50.0, 30.0, 2.0, 10, "1 tbsp", "Indonesian condiment"),
    ("Serundeng", 400, 8.0, 40.0, 23.0, 3.0, 30, "1 portion", "Indonesian condiment"),
    ("Abon sapi (beef floss)", 420, 30.0, 20.0, 25.0, 0.5, 20, "1 tbsp", "Indonesian condiment"),
    ("Abon ayam (chicken floss)", 400, 28.0, 22.0, 22.0, 0.5, 20, "1 tbsp", "Indonesian condiment"),
    # --- snacks and street food ---
    ("Pisang goreng (fried banana)", 250, 2.5, 35.0, 11.0, 1.5, 100, "1 piece", "Indonesian snack"),
    ("Pisang molen", 280, 3.0, 38.0, 13.0, 1.5, 100, "1 piece", "Indonesian snack"),
    ("Bakwan (vegetable fritter)", 220, 4.0, 22.0, 13.0, 1.8, 100, "1 piece", "Indonesian snack"),
    ("Cireng", 240, 2.0, 38.0, 9.0, 1.0, 100, "1 portion", "Indonesian snack"),
    ("Cimol", 230, 2.0, 37.0, 8.5, 1.0, 100, "1 portion", "Indonesian snack"),
    ("Combro", 210, 2.5, 30.0, 9.0, 2.0, 100, "1 piece", "Indonesian snack"),
    ("Misro", 260, 2.5, 40.0, 10.0, 2.0, 100, "1 piece", "Indonesian snack"),
    ("Risoles", 220, 6.0, 22.0, 12.0, 1.2, 100, "1 piece", "Indonesian snack"),
    ("Pastel", 240, 5.0, 26.0, 13.0, 1.5, 100, "1 piece", "Indonesian snack"),
    ("Lumpia", 230, 6.0, 24.0, 12.0, 1.5, 100, "1 piece", "Indonesian snack"),
    ("Martabak telur (savoury)", 250, 10.0, 20.0, 15.0, 1.5, 150, "1 slice", "Indonesian snack"),
    ("Martabak manis (sweet)", 340, 6.0, 48.0, 14.0, 1.5, 100, "1 slice", "Indonesian snack"),
    ("Klepon", 180, 2.0, 34.0, 4.0, 1.5, 100, "1 portion", "Indonesian snack"),
    ("Onde-onde", 250, 3.0, 38.0, 9.5, 1.5, 100, "1 piece", "Indonesian snack"),
    ("Serabi", 200, 3.0, 32.0, 6.5, 1.0, 100, "1 piece", "Indonesian snack"),
    ("Kue putu", 170, 2.0, 33.0, 3.5, 1.0, 100, "1 piece", "Indonesian snack"),
    ("Getuk", 190, 1.5, 42.0, 1.5, 2.0, 100, "1 portion", "Indonesian snack"),
    ("Nagasari", 180, 2.5, 33.0, 4.5, 1.2, 100, "1 piece", "Indonesian snack"),
    ("Bika ambon", 280, 4.0, 45.0, 9.0, 1.0, 100, "1 slice", "Indonesian snack"),
    ("Kue lapis", 200, 2.0, 40.0, 4.0, 1.0, 100, "1 slice", "Indonesian snack"),
    ("Kue cubit", 210, 4.0, 32.0, 7.5, 1.0, 100, "1 portion", "Indonesian snack"),
    ("Roti bakar (filled toast)", 300, 6.0, 40.0, 13.0, 1.5, 100, "1 portion", "Indonesian snack"),
    ("Tahu gejrot", 140, 8.0, 12.0, 7.0, 1.0, 150, "1 portion", "Indonesian snack"),
    ("Batagor", 210, 10.0, 20.0, 10.0, 1.5, 150, "1 portion", "Indonesian snack"),
    ("Siomay", 160, 9.0, 18.0, 6.0, 1.5, 150, "1 portion", "Indonesian snack"),
    # --- drinks ---
    ("Es teh manis (sweet iced tea)", 30, 0.0, 7.5, 0.0, 0.0, 250, "1 glass", "Indonesian drink"),
    ("Teh tawar (unsweetened tea)", 1, 0.0, 0.3, 0.0, 0.0, 250, "1 glass", "Indonesian drink"),
    ("Es jeruk (iced orange)", 40, 0.2, 10.0, 0.0, 0.1, 250, "1 glass", "Indonesian drink"),
    ("Es kelapa muda (young coconut)", 20, 0.3, 4.5, 0.2, 0.3, 300, "1 glass", "Indonesian drink"),
    ("Es cendol / dawet", 130, 1.0, 26.0, 3.0, 0.5, 250, "1 glass", "Indonesian drink"),
    ("Es doger", 150, 2.5, 24.0, 5.0, 0.8, 250, "1 glass", "Indonesian drink"),
    ("Es campur", 140, 2.0, 26.0, 3.5, 1.0, 250, "1 glass", "Indonesian drink"),
    ("Es teler", 160, 2.5, 24.0, 6.0, 1.5, 250, "1 glass", "Indonesian drink"),
    ("Es cincau", 90, 0.5, 20.0, 1.5, 1.5, 250, "1 glass", "Indonesian drink"),
    ("Es kacang hijau", 140, 4.0, 25.0, 3.0, 2.5, 250, "1 glass", "Indonesian drink"),
    ("Es pisang ijo", 170, 2.5, 30.0, 5.0, 1.2, 250, "1 glass", "Indonesian drink"),
    ("Es kopyor", 150, 2.0, 20.0, 7.0, 0.8, 250, "1 glass", "Indonesian drink"),
    ("Es blewah", 55, 0.5, 13.0, 0.2, 0.5, 250, "1 glass", "Indonesian drink"),
    ("Es buah", 90, 0.8, 21.0, 0.5, 1.0, 250, "1 glass", "Indonesian drink"),
    ("Es shanghai", 120, 1.5, 22.0, 3.0, 0.8, 250, "1 glass", "Indonesian drink"),
    ("Cincau hitam (grass jelly drink)", 70, 0.3, 17.0, 0.1, 1.0, 250, "1 glass", "Indonesian drink"),
    ("Wedang jahe (ginger drink)", 45, 0.2, 11.0, 0.1, 0.2, 200, "1 glass", "Indonesian drink"),
    ("Bandrek", 80, 0.8, 17.0, 1.2, 0.3, 200, "1 glass", "Indonesian drink"),
    ("Bajigur", 110, 1.5, 16.0, 4.5, 0.5, 200, "1 glass", "Indonesian drink"),
    ("Sekoteng", 90, 1.5, 16.0, 2.5, 0.8, 250, "1 glass", "Indonesian drink"),
    ("Wedang uwuh", 50, 0.2, 12.0, 0.1, 0.3, 200, "1 glass", "Indonesian drink"),
    ("Wedang ronde", 150, 2.0, 26.0, 4.5, 0.8, 250, "1 bowl", "Indonesian drink"),
    ("Beras kencur", 60, 0.3, 14.0, 0.2, 0.3, 200, "1 glass", "Indonesian drink"),
    ("Kunyit asam", 55, 0.2, 13.5, 0.1, 0.3, 200, "1 glass", "Indonesian drink"),
    ("Temulawak", 50, 0.2, 12.0, 0.1, 0.3, 200, "1 glass", "Indonesian drink"),
    ("Es sinom", 55, 0.2, 13.5, 0.1, 0.3, 200, "1 glass", "Indonesian drink"),
    ("Kopi tubruk (black coffee)", 5, 0.3, 0.5, 0.0, 0.0, 150, "1 cup", "Indonesian drink"),
    ("Kopi susu (coffee with milk)", 60, 2.0, 8.0, 2.0, 0.0, 200, "1 cup", "Indonesian drink"),
    ("Es kopi susu gula aren", 85, 2.0, 13.0, 2.8, 0.0, 250, "1 cup", "Indonesian drink"),
    ("Teh botol (bottled sweet tea)", 40, 0.0, 10.0, 0.0, 0.0, 350, "1 bottle", "Indonesian drink"),
    ("Sari kedelai (soy milk)", 40, 3.3, 4.0, 1.5, 0.4, 250, "1 glass", "Indonesian drink"),
    ("Jus alpukat (avocado juice)", 110, 1.5, 12.0, 6.5, 2.0, 300, "1 glass", "Indonesian drink"),
    ("Jus mangga (mango juice)", 60, 0.5, 14.5, 0.2, 0.5, 300, "1 glass", "Indonesian drink"),
    ("Jus jeruk (orange juice)", 45, 0.7, 10.4, 0.2, 0.2, 300, "1 glass", "Indonesian drink"),
    ("Jus wortel (carrot juice)", 40, 0.9, 9.0, 0.2, 0.8, 300, "1 glass", "Indonesian drink"),
    ("Jus tomat (tomato juice)", 20, 0.8, 4.0, 0.1, 0.4, 300, "1 glass", "Indonesian drink"),
    ("Susu jahe", 70, 2.5, 9.0, 2.5, 0.1, 200, "1 glass", "Indonesian drink"),
    ("Es krim (ice cream)", 210, 3.5, 24.0, 11.0, 0.5, 100, "1 scoop", "Indonesian drink"),
    ("Es potong", 190, 3.0, 26.0, 8.0, 0.5, 100, "1 piece", "Indonesian drink"),
]

SOURCE_NAME = "Tabel Komposisi Pangan Indonesia (TKPI)"
SOURCE_DEFAULTS = {
    "url": "https://panganku.org/",
    "license": "Public (Indonesian Ministry of Health food composition table)",
    "notes": "Per 100 g, rounded. Whole ingredients are table values; cooked composite "
             "dishes are estimates because recipes vary.",
}


def get_or_create(db, model, defaults=None, **kwargs):
    obj = db.scalar(select(model).filter_by(**kwargs))
    if obj:
        return obj, False
    obj = model(**kwargs, **(defaults or {}))
    db.add(obj)
    db.flush()
    return obj, True


def main():
    db = SessionLocal()
    try:
        src, _ = get_or_create(db, FoodSource, name=SOURCE_NAME, defaults=SOURCE_DEFAULTS)
        foods = 0
        # (rows, data_quality, is_verified): table values are reported/verified,
        # cooked dishes are estimates and deliberately left unverified.
        for rows, quality, verified in ((WHOLE, "reported", True), (DISHES, "estimated", False)):
            for name, kcal, p, c, f, fib, sg, slabel, category in rows:
                food, created = get_or_create(
                    db, Food, name=name,
                    defaults={
                        "source_id": src.id, "category": category,
                        "calories_kcal": kcal, "protein_g": p, "carbs_g": c, "fat_g": f,
                        "fiber_g": fib, "default_serving_g": sg, "default_serving_label": slabel,
                        "data_quality": quality, "is_verified": verified,
                    },
                )
                if created:
                    foods += 1
                    db.add(FoodServing(food_id=food.id, label=slabel, grams=sg, is_default=True))
        db.commit()
        total_foods = len(list(db.scalars(select(Food))))
        print(f"catalogue_indonesia: foods+{foods}")
        print(f"totals: foods={total_foods}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
