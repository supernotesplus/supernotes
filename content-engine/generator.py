import csv
import os
import random
import json
from datetime import datetime
from slugify import slugify # هذه المكتبة ستقوم بتحويل العناوين إلى أسماء ملفات URL آمنة

# ----------------------------------------------------
# 1. إعدادات المسارات
# ----------------------------------------------------
CONFIG_FILE = 'content-engine/config.json'
CONTENT_DIR = 'content/posts'
BLOCKS_DIR = 'blocks'

def load_config():
    """تحميل إعدادات العمق والحد اليومي من config.json"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ خطأ: فشل في تحميل config.json: {e}")
        return None

def load_blocks(section_name):
    """تحميل جميع البلوكات من ملف القسم المحدد"""
    filepath = os.path.join(BLOCKS_DIR, f'{section_name}.txt')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # استخدام list comprehension لإزالة الأسطر الفارغة
            blocks = [line.strip() for line in f if line.strip()]
        return blocks
    except FileNotFoundError:
        print(f"⚠️ تحذير: لم يتم العثور على ملف البلوكات: {filepath}")
        return []

def generate_article(keyword, title, blocks_map, depth_config):
    """توليد مقال واحد باستخدام البلوكات وإعدادات العمق"""
    
    # ----------------------------------------------------
    # 2. بناء الأقسام (باستخدام random.sample لفرض العمق)
    # ----------------------------------------------------
    
    # قائمة بأسماء الأقسام بالترتيب الذي تريده في المقال
    section_order = ['intros', 'explanations', 'pros', 'cons', 'steps', 'tips', 'cta']
    
    article_content = []

    for section in section_order:
        # تحديد العمق (عدد البلوكات المطلوب سحبها) من config.json
        required_depth = depth_config.get(section, 1) # الافتراضي هو 1 إذا لم يجد الإعداد
        
        available_blocks = blocks_map.get(section, [])
        
        if not available_blocks:
            continue
        
        # نستخدم random.sample لاختيار عدد معين من البلوكات
        # إذا كان العمق المطلوب أكبر من البلوكات المتاحة، نختار كل المتاح
        num_blocks_to_select = min(required_depth, len(available_blocks))
        
        if num_blocks_to_select == 0:
            continue
            
        selected_blocks = random.sample(available_blocks, num_blocks_to_select)
        
        # 3. تنسيق المحتوى لـ Markdown
        
        # إضافة عنوان القسم (باستثناء المقدمة والخاتمة)
        if section not in ['intros', 'cta']:
            # نحول أسماء الأقسام إلى عناوين مقروءة (مثل: steps -> Practical Steps)
            readable_title = {
                'explanations': 'Key Explanations and Context',
                'pros': 'Benefits and Advantages',
                'cons': 'Challenges and Considerations',
                'steps': 'Practical Steps To Implement',
                'tips': 'Expert Tips And Insights',
            }.get(section, section.capitalize())
            
            article_content.append(f'\n## {readable_title}\n')
            
        # دمج البلوكات المحددة
        # كل بلوك يتم وضعه في فقرة منفصلة
        for block in selected_blocks:
            article_content.append(f'{block}\n')
            
    # ----------------------------------------------------
    # 4. بناء الـ Front Matter (بيانات Hugo)
    # ----------------------------------------------------
    
    # استخدام العنوان لإنشاء اسم ملف آمن
    filename_slug = slugify(title)
    filename = os.path.join(CONTENT_DIR, f'{filename_slug}.md')
    
    # نستخدم الكلمات المفتاحية كعلامات (Tags)
    tags = [slugify(keyword, separator=' ')]
    
    front_matter = f"""---
title: "{title}"
date: {datetime.now().isoformat()}
draft: false
tags: {json.dumps(tags)}
keywords: ["{keyword}"]
categories: ["Knowledge"]
---
"""
    
    # 5. دمج الـ Front Matter والمحتوى
    final_content = front_matter + '\n' + '\n'.join(article_content)
    
    # 6. حفظ الملف
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"✅ تم توليد المقال: {filename}")
        return filename
    except Exception as e:
        print(f"❌ فشل في حفظ الملف {filename}: {e}")
        return None


def main():
    config = load_config()
    if not config:
        return

    keywords_file = os.path.join('content-engine', config.get('keywords_file', 'new_keywords.csv'))
    daily_limit = config.get('daily_limit', 1)
    depth_config = config.get('section_depth', {})
    
    # 1. تحميل البلوكات مرة واحدة
    blocks_map = {}
    for section in depth_config.keys():
        blocks_map[section] = load_blocks(section)
        
    # التحقق من وجود بيانات كافية
    total_available_blocks = sum(len(blocks) for blocks in blocks_map.values())
    if total_available_blocks < 10:
        print("🛑 فشل في التشغيل: لا يوجد عدد كافٍ من البلوكات في مجلد blocks/.")
        return

    # 2. تحميل الكلمات المفتاحية
    try:
        with open(keywords_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            all_keywords = list(reader)
    except FileNotFoundError:
        print(f"🛑 فشل في التشغيل: لم يتم العثور على ملف الكلمات المفتاحية: {keywords_file}")
        return

    if not all_keywords:
        print("🛑 لا توجد كلمات مفتاحية جديدة للتوليد.")
        return

    # 3. اختيار المقالات للتوليد بناءً على الحد اليومي
    posts_to_generate = all_keywords[:daily_limit]
    
    print(f"📝 بدء توليد {len(posts_to_generate)} مقال من أصل {len(all_keywords)} متاحين...")
    
    # 4. توليد المقالات وحذف الأسطر التي تم استخدامها
    generated_count = 0
    generated_filenames = []
    
    for post in posts_to_generate:
        filename = generate_article(post['keyword'], post['title'], blocks_map, depth_config)
        if filename:
            generated_count += 1
            generated_filenames.append(filename)

    # 5. حذف الأسطر التي تم توليدها من ملف CSV
    remaining_keywords = all_keywords[generated_count:]
    
    try:
        with open(keywords_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['keyword', 'title']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(remaining_keywords)
        print(f"✅ تم تحديث ملف الكلمات المفتاحية. تبقت {len(remaining_keywords)} كلمة.")
    except Exception as e:
        print(f"❌ فشل في تحديث ملف CSV: {e}")
        
    print(f"--- انتهت عملية توليد المحتوى. تم إنشاء {generated_count} مقال. ---")


if __name__ == '__main__':
    main()
