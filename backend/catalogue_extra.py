#!/usr/bin/env python3
"""TRINITY catalogue extension: extra gym exercises and extra foods/drinks.
Idempotent (get_or_create by name), safe to run against a live database.
Usage: python catalogue_extra.py
"""
import sys

sys.path.insert(0, ".")

from sqlalchemy import select  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402
from app.models.nutrition import Food, FoodServing, FoodSource  # noqa: E402
from app.models.training import ExerciseLibrary  # noqa: E402

# name, kcal, protein, carbs, fat, fiber, serving_g, serving_label  (per 100 g)
FOODS_EXTRA = [
    # --- protein ---
    ("Turkey breast, skinless, raw", 111, 24.0, 0.0, 1.0, 0.0, 170, "1 breast"),
    ("Turkey mince, 93% lean, raw", 150, 20.0, 0.0, 7.5, 0.0, 120, "1 portion"),
    ("Pork loin, lean, raw", 143, 21.0, 0.0, 6.0, 0.0, 150, "1 chop"),
    ("Pork tenderloin, raw", 120, 20.9, 0.0, 3.5, 0.0, 150, "1 portion"),
    ("Lamb leg, lean, raw", 162, 20.0, 0.0, 9.0, 0.0, 150, "1 portion"),
    ("Bison, ground, raw", 146, 20.2, 0.0, 7.0, 0.0, 120, "1 patty"),
    ("Cod, Atlantic, raw", 82, 17.8, 0.0, 0.7, 0.0, 150, "1 fillet"),
    ("Tilapia, raw", 96, 20.1, 0.0, 1.7, 0.0, 150, "1 fillet"),
    ("Shrimp, raw", 85, 20.1, 0.2, 0.5, 0.0, 100, "1 portion"),
    ("Prawns, cooked", 99, 24.0, 0.2, 0.3, 0.0, 100, "1 portion"),
    ("Sardines, canned in oil, drained", 208, 24.6, 0.0, 11.5, 0.0, 90, "1 tin"),
    ("Mackerel, raw", 205, 18.6, 0.0, 13.9, 0.0, 150, "1 fillet"),
    ("Scallops, raw", 88, 16.8, 3.2, 0.8, 0.0, 100, "1 portion"),
    ("Duck breast, skinless, raw", 135, 19.0, 0.0, 6.0, 0.0, 150, "1 breast"),
    ("Beef sirloin steak, lean, raw", 145, 22.0, 0.0, 5.5, 0.0, 200, "1 steak"),
    ("Beef mince, 85% lean, raw", 215, 18.6, 0.0, 15.0, 0.0, 120, "1 patty"),
    ("Beef ribeye, raw", 291, 19.0, 0.0, 23.0, 0.0, 225, "1 steak"),
    ("Chicken wings, raw", 191, 18.0, 0.0, 12.8, 0.0, 120, "4 wings"),
    ("Chicken drumstick, skinless, raw", 120, 20.0, 0.0, 4.0, 0.0, 100, "1 drumstick"),
    ("Turkey bacon", 368, 29.0, 1.0, 27.0, 0.0, 30, "2 rashers"),
    ("Ham, lean, sliced", 116, 20.0, 1.5, 3.0, 0.0, 60, "2 slices"),
    ("Bacon, back, grilled", 269, 24.0, 0.0, 19.0, 0.0, 40, "2 rashers"),
    ("Sausage, pork, cooked", 300, 15.0, 2.0, 26.0, 0.0, 60, "1 sausage"),
    ("Protein bar, whey", 350, 30.0, 35.0, 10.0, 6.0, 60, "1 bar"),
    ("Casein protein powder", 360, 78.0, 6.0, 1.5, 0.0, 30, "1 scoop"),
    ("Tempeh, cooked", 195, 19.9, 7.6, 11.4, 5.0, 100, "1 portion"),
    ("Seitan", 141, 25.0, 14.0, 2.0, 1.0, 100, "1 portion"),
    ("Edamame, cooked", 122, 11.9, 9.9, 5.2, 5.2, 155, "1 cup"),
    ("Kidney beans, cooked", 127, 8.7, 22.8, 0.5, 6.4, 177, "1 cup"),
    ("Pinto beans, cooked", 143, 9.0, 26.2, 0.6, 9.0, 171, "1 cup"),
    ("Navy beans, cooked", 140, 8.2, 26.0, 0.6, 10.5, 182, "1 cup"),
    ("Soy milk, unsweetened", 33, 3.3, 0.7, 1.8, 0.5, 250, "1 glass"),
    ("Textured vegetable protein, dry", 327, 50.0, 20.0, 1.0, 18.0, 25, "1 serving"),
    # --- carbs ---
    ("Quinoa, cooked", 120, 4.4, 21.3, 1.9, 2.8, 185, "1 cup"),
    ("Couscous, cooked", 112, 3.8, 23.2, 0.2, 1.4, 157, "1 cup"),
    ("Bulgur, cooked", 83, 3.1, 18.6, 0.2, 4.5, 182, "1 cup"),
    ("Pearl barley, cooked", 123, 2.3, 28.2, 0.4, 3.8, 157, "1 cup"),
    ("Buckwheat, cooked", 92, 3.4, 19.9, 0.6, 2.7, 168, "1 cup"),
    ("Bread, white", 265, 9.0, 49.0, 3.2, 2.7, 36, "1 slice"),
    ("Bread, sourdough", 274, 10.0, 52.0, 1.7, 2.4, 50, "1 slice"),
    ("Bagel, plain", 250, 10.0, 49.0, 1.5, 2.0, 85, "1 bagel"),
    ("Tortilla, flour", 300, 8.0, 51.0, 7.0, 3.0, 45, "1 tortilla"),
    ("Tortilla, corn", 218, 5.7, 45.0, 2.9, 6.3, 26, "1 tortilla"),
    ("Rice cakes", 387, 8.2, 81.5, 2.8, 4.2, 9, "1 cake"),
    ("Cream of rice, dry", 360, 7.0, 80.0, 0.5, 1.0, 45, "1 serving"),
    ("Cornflakes", 357, 7.5, 84.0, 0.4, 3.0, 30, "1 serving"),
    ("Granola", 471, 10.0, 64.0, 20.0, 7.0, 45, "1 serving"),
    ("Muesli", 362, 10.0, 66.0, 6.0, 8.0, 50, "1 serving"),
    ("Potato, baked with skin", 93, 2.5, 21.0, 0.1, 2.2, 200, "1 medium"),
    ("Sweet potato, mashed", 88, 1.6, 20.0, 0.2, 3.0, 200, "1 portion"),
    ("Yam, cooked", 116, 1.5, 27.5, 0.1, 4.1, 150, "1 portion"),
    ("Plantain, cooked", 116, 1.3, 31.0, 0.2, 2.3, 150, "1 plantain"),
    ("Polenta, cooked", 85, 2.0, 18.0, 0.4, 1.0, 200, "1 portion"),
    ("Rice noodles, cooked", 108, 1.8, 24.9, 0.2, 1.0, 176, "1 cup"),
    ("Soba noodles, cooked", 99, 5.1, 21.4, 0.1, 0.0, 176, "1 cup"),
    ("Ramen noodles, cooked", 138, 4.5, 25.0, 2.0, 1.2, 176, "1 cup"),
    ("Pasta, white, cooked", 158, 5.8, 30.9, 0.9, 1.8, 140, "1 cup"),
    ("Gnocchi, cooked", 133, 3.0, 27.0, 0.8, 1.5, 150, "1 portion"),
    ("Baguette", 274, 9.0, 55.0, 1.0, 2.5, 60, "1 portion"),
    ("Pita bread", 275, 9.0, 55.0, 1.2, 2.4, 60, "1 pita"),
    ("Naan bread", 310, 8.7, 50.0, 7.5, 2.0, 90, "1 naan"),
    ("Croissant", 406, 8.2, 45.8, 21.0, 2.6, 60, "1 croissant"),
    ("Muffin, blueberry", 375, 5.0, 54.0, 15.0, 1.5, 100, "1 muffin"),
    ("Pancake, plain", 227, 6.0, 28.0, 9.0, 1.0, 60, "1 pancake"),
    ("Waffle, plain", 291, 8.0, 33.0, 14.0, 1.5, 75, "1 waffle"),
    # --- vegetables ---
    ("Asparagus, cooked", 22, 2.4, 3.9, 0.2, 2.0, 90, "1 cup"),
    ("Green beans, cooked", 35, 1.8, 7.9, 0.1, 3.4, 125, "1 cup"),
    ("Zucchini, cooked", 15, 1.1, 2.7, 0.3, 1.0, 124, "1 cup"),
    ("Cauliflower, cooked", 23, 1.8, 4.1, 0.5, 2.1, 107, "1 cup"),
    ("Carrot, raw", 41, 0.9, 9.6, 0.2, 2.8, 61, "1 carrot"),
    ("Bell pepper, red, raw", 31, 1.0, 6.0, 0.3, 2.1, 119, "1 pepper"),
    ("Tomato, raw", 18, 0.9, 3.9, 0.2, 1.2, 123, "1 tomato"),
    ("Cucumber, raw", 15, 0.7, 3.6, 0.1, 0.5, 100, "1 portion"),
    ("Lettuce, romaine", 17, 1.2, 3.3, 0.3, 2.1, 47, "1 cup"),
    ("Kale, cooked", 28, 1.9, 5.6, 0.4, 2.0, 67, "1 cup"),
    ("Cabbage, cooked", 23, 1.3, 5.5, 0.1, 1.9, 89, "1 cup"),
    ("Brussels sprouts, cooked", 36, 2.6, 7.1, 0.5, 2.6, 88, "1 cup"),
    ("Mushrooms, cooked", 28, 2.2, 5.3, 0.5, 2.2, 78, "1 cup"),
    ("Onion, raw", 40, 1.1, 9.3, 0.1, 1.7, 110, "1 onion"),
    ("Beetroot, cooked", 44, 1.7, 10.0, 0.2, 2.0, 136, "1 cup"),
    ("Peas, green, cooked", 84, 5.4, 15.6, 0.2, 5.5, 160, "1 cup"),
    ("Sweetcorn, cooked", 96, 3.4, 21.0, 1.5, 2.4, 165, "1 cup"),
    ("Eggplant, cooked", 35, 0.8, 8.6, 0.2, 2.5, 99, "1 cup"),
    ("Celery, raw", 16, 0.7, 3.0, 0.2, 1.6, 40, "2 stalks"),
    ("Okra, cooked", 22, 1.9, 4.5, 0.2, 2.5, 100, "1 cup"),
    ("Radish, raw", 16, 0.7, 3.4, 0.1, 1.6, 58, "1 cup"),
    ("Rocket, raw", 25, 2.6, 3.7, 0.7, 1.6, 20, "1 handful"),
    # --- fruit ---
    ("Mango, raw", 60, 0.8, 15.0, 0.4, 1.6, 165, "1 mango"),
    ("Pineapple, raw", 50, 0.5, 13.1, 0.1, 1.4, 165, "1 cup"),
    ("Grapes, raw", 69, 0.7, 18.1, 0.2, 0.9, 151, "1 cup"),
    ("Watermelon, raw", 30, 0.6, 7.6, 0.2, 0.4, 152, "1 slice"),
    ("Cantaloupe, raw", 34, 0.8, 8.2, 0.2, 0.9, 160, "1 cup"),
    ("Kiwi, raw", 61, 1.1, 14.7, 0.5, 3.0, 69, "1 kiwi"),
    ("Pear, raw", 57, 0.4, 15.2, 0.1, 3.1, 178, "1 pear"),
    ("Peach, raw", 39, 0.9, 9.5, 0.3, 1.5, 150, "1 peach"),
    ("Plum, raw", 46, 0.7, 11.4, 0.3, 1.4, 66, "1 plum"),
    ("Cherries, raw", 63, 1.1, 16.0, 0.2, 2.1, 154, "1 cup"),
    ("Raspberries, raw", 52, 1.2, 11.9, 0.7, 6.5, 123, "1 cup"),
    ("Blackberries, raw", 43, 1.4, 9.6, 0.5, 5.3, 144, "1 cup"),
    ("Pomegranate, raw", 83, 1.7, 18.7, 1.2, 4.0, 174, "1 cup"),
    ("Dates, medjool", 277, 1.8, 75.0, 0.2, 6.7, 24, "2 dates"),
    ("Figs, raw", 74, 0.8, 19.2, 0.3, 2.9, 50, "1 fig"),
    ("Raisins", 299, 3.1, 79.2, 0.5, 3.7, 30, "1 handful"),
    ("Dried apricots", 241, 3.4, 62.6, 0.5, 7.3, 30, "1 handful"),
    ("Papaya, raw", 43, 0.5, 10.8, 0.3, 1.7, 145, "1 cup"),
    ("Passion fruit, raw", 97, 2.2, 23.4, 0.7, 10.4, 18, "1 fruit"),
    ("Coconut, fresh", 354, 3.3, 15.2, 33.5, 9.0, 45, "1 portion"),
    ("Lemon, raw", 29, 1.1, 9.3, 0.3, 2.8, 58, "1 lemon"),
    # --- dairy ---
    ("Milk, whole", 61, 3.2, 4.8, 3.3, 0.0, 250, "1 glass"),
    ("Milk, skim", 34, 3.4, 5.0, 0.1, 0.0, 250, "1 glass"),
    ("Oat milk", 46, 1.0, 7.0, 1.5, 0.8, 250, "1 glass"),
    ("Almond milk, unsweetened", 15, 0.6, 0.3, 1.2, 0.3, 250, "1 glass"),
    ("Kefir, plain", 41, 3.3, 4.7, 1.0, 0.0, 250, "1 glass"),
    ("Skyr, plain", 63, 11.0, 4.0, 0.2, 0.0, 150, "1 pot"),
    ("Quark, low-fat", 67, 12.0, 4.0, 0.2, 0.0, 150, "1 pot"),
    ("Cheddar cheese", 403, 25.0, 1.3, 33.0, 0.0, 30, "1 slice"),
    ("Mozzarella", 280, 28.0, 3.1, 17.0, 0.0, 30, "1 slice"),
    ("Parmesan, grated", 431, 38.0, 4.1, 29.0, 0.0, 15, "1 tbsp"),
    ("Feta cheese", 264, 14.2, 4.1, 21.3, 0.0, 30, "1 portion"),
    ("Halloumi", 321, 22.0, 2.0, 25.0, 0.0, 30, "1 slice"),
    ("Cream cheese", 342, 6.2, 4.1, 34.0, 0.0, 30, "1 tbsp"),
    ("Butter, salted", 717, 0.9, 0.1, 81.1, 0.0, 10, "1 tsp"),
    ("Double cream", 449, 2.1, 2.8, 48.0, 0.0, 15, "1 tbsp"),
    ("Ice cream, vanilla", 207, 3.5, 23.6, 11.0, 0.7, 60, "1 scoop"),
    # --- nuts, seeds, fats ---
    ("Walnuts, raw", 654, 15.2, 13.7, 65.2, 6.7, 28, "1 handful"),
    ("Cashews, raw", 553, 18.2, 30.2, 43.9, 3.3, 28, "1 handful"),
    ("Pistachios, raw", 560, 20.2, 27.2, 45.3, 10.6, 28, "1 handful"),
    ("Pecans, raw", 691, 9.2, 13.9, 72.0, 9.6, 28, "1 handful"),
    ("Macadamia nuts", 718, 7.9, 13.8, 75.8, 8.6, 28, "1 handful"),
    ("Brazil nuts", 659, 14.3, 11.7, 67.1, 7.5, 28, "1 handful"),
    ("Sunflower seeds", 584, 20.8, 20.0, 51.5, 8.6, 28, "1 handful"),
    ("Pumpkin seeds", 559, 30.2, 10.7, 49.0, 6.0, 28, "1 handful"),
    ("Chia seeds", 486, 16.5, 42.1, 30.7, 34.4, 20, "1 tbsp"),
    ("Flaxseed, ground", 534, 18.3, 28.9, 42.2, 27.3, 15, "1 tbsp"),
    ("Hemp seeds", 553, 31.6, 8.7, 48.8, 4.0, 20, "1 tbsp"),
    ("Sesame seeds", 573, 17.7, 23.4, 49.7, 11.8, 15, "1 tbsp"),
    ("Tahini", 595, 17.0, 21.2, 53.8, 9.3, 15, "1 tbsp"),
    ("Almond butter", 614, 21.0, 18.8, 55.5, 10.3, 32, "2 tbsp"),
    ("Coconut oil", 892, 0.0, 0.0, 99.1, 0.0, 14, "1 tbsp"),
    ("Ghee", 876, 0.0, 0.0, 99.5, 0.0, 14, "1 tbsp"),
    ("Avocado oil", 884, 0.0, 0.0, 100.0, 0.0, 14, "1 tbsp"),
    ("Rapeseed oil", 884, 0.0, 0.0, 100.0, 0.0, 14, "1 tbsp"),
    ("Mayonnaise", 680, 1.0, 0.6, 75.0, 0.0, 15, "1 tbsp"),
    # --- snacks and sweets ---
    ("Milk chocolate", 535, 7.6, 59.4, 29.7, 3.4, 25, "4 squares"),
    ("Honey", 304, 0.3, 82.4, 0.0, 0.2, 21, "1 tbsp"),
    ("Maple syrup", 260, 0.0, 67.0, 0.1, 0.0, 20, "1 tbsp"),
    ("Strawberry jam", 278, 0.4, 68.9, 0.1, 1.0, 20, "1 tbsp"),
    ("Chocolate hazelnut spread", 539, 6.3, 57.5, 30.9, 5.4, 20, "1 tbsp"),
    ("Digestive biscuit", 480, 7.0, 65.0, 21.0, 3.0, 15, "1 biscuit"),
    ("Potato crisps", 536, 7.0, 53.0, 34.0, 4.8, 30, "1 bag"),
    ("Popcorn, plain", 387, 12.9, 77.8, 4.5, 14.5, 30, "1 portion"),
    ("Pretzels", 380, 10.0, 80.0, 2.6, 3.0, 30, "1 portion"),
    ("Granola bar", 471, 10.0, 64.0, 20.0, 5.0, 40, "1 bar"),
    # --- drinks ---
    ("Water", 0, 0.0, 0.0, 0.0, 0.0, 250, "1 glass"),
    ("Sparkling water", 0, 0.0, 0.0, 0.0, 0.0, 250, "1 glass"),
    ("Coffee, black", 2, 0.1, 0.0, 0.0, 0.0, 250, "1 cup"),
    ("Espresso", 9, 0.5, 1.7, 0.2, 0.0, 30, "1 shot"),
    ("Latte, whole milk", 55, 3.0, 4.5, 2.8, 0.0, 300, "1 cup"),
    ("Cappuccino", 40, 2.2, 3.3, 1.8, 0.0, 200, "1 cup"),
    ("Green tea", 1, 0.0, 0.2, 0.0, 0.0, 250, "1 cup"),
    ("Black tea", 1, 0.0, 0.3, 0.0, 0.0, 250, "1 cup"),
    ("Herbal tea", 0, 0.0, 0.0, 0.0, 0.0, 250, "1 cup"),
    ("Orange juice", 45, 0.7, 10.4, 0.2, 0.2, 250, "1 glass"),
    ("Apple juice", 46, 0.1, 11.3, 0.1, 0.2, 250, "1 glass"),
    ("Cranberry juice", 46, 0.4, 11.6, 0.1, 0.1, 250, "1 glass"),
    ("Tomato juice", 17, 0.8, 3.5, 0.1, 0.4, 250, "1 glass"),
    ("Cola", 42, 0.0, 10.6, 0.0, 0.0, 330, "1 can"),
    ("Diet cola", 0, 0.0, 0.0, 0.0, 0.0, 330, "1 can"),
    ("Lemonade", 40, 0.0, 10.0, 0.0, 0.0, 250, "1 glass"),
    ("Sports drink, electrolyte", 26, 0.0, 6.5, 0.0, 0.0, 500, "1 bottle"),
    ("Energy drink", 45, 0.4, 11.0, 0.0, 0.0, 250, "1 can"),
    ("Beer, lager", 43, 0.5, 3.6, 0.0, 0.0, 330, "1 bottle"),
    ("Wine, red", 85, 0.1, 2.6, 0.0, 0.0, 175, "1 glass"),
    ("Wine, white", 82, 0.1, 2.6, 0.0, 0.0, 175, "1 glass"),
    ("Vodka", 231, 0.0, 0.0, 0.0, 0.0, 25, "1 shot"),
    ("Kombucha", 5, 0.0, 1.3, 0.0, 0.0, 250, "1 glass"),
    ("Coconut water", 19, 0.7, 3.7, 0.2, 1.1, 250, "1 glass"),
    ("Smoothie, berry", 60, 1.5, 13.0, 0.5, 1.5, 300, "1 glass"),
    ("Protein shake, ready-to-drink", 60, 10.0, 3.0, 1.0, 0.0, 330, "1 bottle"),
    ("Milkshake, vanilla", 112, 3.4, 17.8, 3.0, 0.0, 300, "1 glass"),
    # --- composite meals ---
    ("Pizza, cheese, thin crust", 266, 11.0, 33.0, 10.0, 2.3, 100, "1 slice"),
    ("Beef burger, fast food", 254, 12.0, 30.0, 9.0, 1.5, 200, "1 burger"),
    ("French fries", 312, 3.4, 41.0, 15.0, 3.8, 120, "1 portion"),
    ("Sushi roll, salmon", 145, 6.0, 26.0, 1.5, 1.0, 200, "6 pieces"),
    ("Chicken shawarma wrap", 210, 14.0, 20.0, 8.0, 2.0, 250, "1 wrap"),
    ("Burrito, chicken", 190, 10.0, 24.0, 6.0, 2.5, 300, "1 burrito"),
    ("Pad thai", 180, 8.0, 24.0, 5.5, 1.8, 300, "1 portion"),
    ("Chicken curry", 150, 12.0, 7.0, 8.0, 1.5, 300, "1 portion"),
    ("Fried rice, chicken", 168, 7.5, 24.0, 4.5, 1.2, 300, "1 portion"),
    ("Caesar salad, chicken", 130, 11.0, 5.0, 7.0, 1.5, 250, "1 bowl"),
    ("Omelette, cheese", 168, 11.5, 1.5, 13.0, 0.0, 150, "1 omelette"),
    ("Scrambled eggs", 149, 10.0, 1.6, 11.0, 0.0, 120, "2 eggs"),
    ("Protein pancakes", 190, 15.0, 20.0, 5.0, 2.0, 150, "3 pancakes"),
    ("Beef lasagne", 135, 7.5, 12.0, 6.5, 1.2, 300, "1 portion"),
    ("Chicken caesar wrap", 200, 13.0, 19.0, 8.0, 1.8, 220, "1 wrap"),
]

# name, primary muscle, secondary, equipment, pattern
EXERCISES_EXTRA = [
    ("Hack Squat", "Quads", "Glutes", "Machine", "squat"),
    ("Pendulum Squat", "Quads", "Glutes", "Machine", "squat"),
    ("Smith Machine Squat", "Quads", "Glutes", "Machine", "squat"),
    ("Smith Machine Bench Press", "Chest", "Front Delts,Triceps", "Machine", "push"),
    ("Smith Machine Shoulder Press", "Front Delts", "Triceps", "Machine", "push"),
    ("Smith Machine Row", "Lats", "Biceps", "Machine", "pull"),
    ("Seated Leg Curl", "Hamstrings", "Calves", "Machine", "hinge"),
    ("Standing Leg Curl", "Hamstrings", "Calves", "Machine", "hinge"),
    ("Hip Abduction Machine", "Glutes", "", "Machine", "hinge"),
    ("Hip Adduction Machine", "Adductors", "", "Machine", "hinge"),
    ("Glute Kickback", "Glutes", "Hamstrings", "Cable", "hinge"),
    ("Nordic Curl", "Hamstrings", "Glutes", "Bodyweight", "hinge"),
    ("Good Morning", "Hamstrings", "Lower Back", "Barbell", "hinge"),
    ("Sumo Deadlift", "Hamstrings", "Glutes,Adductors", "Barbell", "hinge"),
    ("Trap Bar Deadlift", "Hamstrings", "Glutes,Quads", "Barbell", "hinge"),
    ("Back Extension", "Lower Back", "Glutes", "Bodyweight", "hinge"),
    ("Reverse Hyperextension", "Glutes", "Hamstrings", "Machine", "hinge"),
    ("Lat Pullover", "Lats", "Chest", "Cable", "pull"),
    ("Single-Arm Lat Pulldown", "Lats", "Biceps", "Cable", "pull"),
    ("Wide-Grip Lat Pulldown", "Lats", "Biceps", "Cable", "pull"),
    ("Straight-Arm Pulldown", "Lats", "Triceps", "Cable", "pull"),
    ("T-Bar Row", "Lats", "Rear Delts,Biceps", "Barbell", "pull"),
    ("Pendlay Row", "Lats", "Rear Delts,Biceps", "Barbell", "pull"),
    ("Chest-Supported Row", "Lats", "Rear Delts,Biceps", "Machine", "pull"),
    ("Machine Row", "Lats", "Biceps", "Machine", "pull"),
    ("Meadows Row", "Lats", "Biceps", "Barbell", "pull"),
    ("Cable Lateral Raise", "Side Delts", "", "Cable", "push"),
    ("Machine Lateral Raise", "Side Delts", "", "Machine", "push"),
    ("Rear Delt Fly", "Rear Delts", "Traps", "Dumbbell", "pull"),
    ("Reverse Pec Deck", "Rear Delts", "Traps", "Machine", "pull"),
    ("Cable Rear Delt Fly", "Rear Delts", "Traps", "Cable", "pull"),
    ("Cable Chest Press", "Chest", "Front Delts,Triceps", "Cable", "push"),
    ("Cable Fly", "Chest", "Front Delts", "Cable", "push"),
    ("Pec Deck", "Chest", "Front Delts", "Machine", "push"),
    ("Chest Press Machine", "Chest", "Front Delts,Triceps", "Machine", "push"),
    ("Incline Barbell Bench Press", "Upper Chest", "Front Delts,Triceps", "Barbell", "push"),
    ("Decline Bench Press", "Lower Chest", "Triceps", "Barbell", "push"),
    ("Dumbbell Shoulder Press", "Front Delts", "Triceps", "Dumbbell", "push"),
    ("Arnold Press", "Front Delts", "Side Delts,Triceps", "Dumbbell", "push"),
    ("Machine Shoulder Press", "Front Delts", "Triceps", "Machine", "push"),
    ("Push-Up", "Chest", "Triceps,Core", "Bodyweight", "push"),
    ("Seated Calf Raise", "Calves", "", "Machine", "carry"),
    ("Donkey Calf Raise", "Calves", "", "Machine", "carry"),
    ("Calf Press", "Calves", "", "Machine", "carry"),
    ("Cable Curl", "Biceps", "Forearms", "Cable", "pull"),
    ("Hammer Curl", "Biceps", "Forearms", "Dumbbell", "pull"),
    ("Preacher Curl", "Biceps", "", "Barbell", "pull"),
    ("Skull Crusher", "Triceps", "", "Barbell", "push"),
    ("Overhead Cable Triceps Extension", "Triceps", "", "Cable", "push"),
    ("Upright Row", "Traps", "Side Delts", "Barbell", "pull"),
    ("Dumbbell Shrug", "Traps", "", "Dumbbell", "carry"),
    ("Ab Wheel Rollout", "Core", "", "Bodyweight", "core"),
    ("Russian Twist", "Core", "", "Bodyweight", "core"),
    ("Side Plank", "Core", "", "Bodyweight", "core"),
    ("Bicycle Crunch", "Core", "", "Bodyweight", "core"),
    ("Dead Bug", "Core", "", "Bodyweight", "core"),
    ("Reverse Crunch", "Core", "", "Bodyweight", "core"),
]


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
        src, _ = get_or_create(
            db, FoodSource, name="USDA FoodData Central",
            defaults={
                "url": "https://fdc.nal.usda.gov/",
                "license": "Public domain (US Government work)",
                "notes": "Values per 100 g, rounded. Foundation/SR Legacy datasets.",
            },
        )
        foods = 0
        for name, kcal, p, c, f, fib, sg, slabel in FOODS_EXTRA:
            food, created = get_or_create(
                db, Food, name=name,
                defaults={
                    "source_id": src.id, "calories_kcal": kcal, "protein_g": p,
                    "carbs_g": c, "fat_g": f, "fiber_g": fib,
                    "default_serving_g": sg, "default_serving_label": slabel,
                    "data_quality": "reported", "is_verified": True,
                },
            )
            if created:
                foods += 1
                db.add(FoodServing(food_id=food.id, label=slabel, grams=sg, is_default=True))
        ex = 0
        for name, pm, sm, eq, pat in EXERCISES_EXTRA:
            _, created = get_or_create(
                db, ExerciseLibrary, name=name,
                defaults={
                    "primary_muscle": pm, "secondary_muscles": sm or None,
                    "equipment": eq, "movement_pattern": pat,
                    "instructions": "Controlled eccentric, full range, brace the core.",
                },
            )
            if created:
                ex += 1
        db.commit()
        total_foods = len(list(db.scalars(select(Food))))
        total_ex = len(list(db.scalars(select(ExerciseLibrary))))
        print(f"catalogue_extra: foods+{foods} exercises+{ex}")
        print(f"totals: foods={total_foods} exercises={total_ex}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
