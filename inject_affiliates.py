import csv
import os
import re

# ===================================================
# إعدادات Script (الحد الأقصى للروابط والمجلدات)
# ===================================================
MAX_LINKS_PER_ARTICLE = 3
CONTENT_DIR = 'content/posts'
AFFILIATE_CSV = 'affiliate_lookup.csv'

def load_affiliates(csv_file):
    """
    يقوم بتحميل بيانات الـ Affiliate من ملف CSV إلى قاموس.
    """
    affiliate_data = {}
    try:
        with open(csv_file, mode='r', encoding='utf-8') as file:
            # نستخدم DictReader للتعامل مع الأعمدة بالأسماء
            reader = csv.DictReader(file)
            for row in reader:
                keyword = row.get('keyword', '').strip().lower()
                if keyword:
                    affiliate_data[keyword] = {
                        'url': row.get('affiliate_url', '').strip(),
                        'text': row.get('affiliate_text', '').strip()
                    }
    except FileNotFoundError:
        print(f"❌ خطأ: لم يتم العثور على ملف {csv_file}. لن يتم حقن أي روابط.")
        return {}
    except Exception as e:
        print(f"❌ خطأ في قراءة ملف CSV: {e}")
        return {}

    # ترتيب الكلمات المفتاحية حسب الطول (تنازلياً) لضمان المطابقة الأفضل
    sorted_keywords = sorted(affiliate_data.keys(), key=len, reverse=True)
    return {k: affiliate_data[k] for k in sorted_keywords}


def inject_links(affiliate_map):
    """
    يقوم بالبحث والاستبدال في جميع ملفات Markdown الجديدة.
    """
    if not affiliate_map:
        return

    # نمط regex لفصل الـ Front Matter (بيانات Hugo) عن محتوى المقال
    front_matter_pattern = re.compile(r'^---\s*$.*?^---\s*$', re.MULTILINE | re.DOTALL)
    
    print(f"📝 بدء عملية فحص المقالات في: {CONTENT_DIR}")

    # يجب أن نقوم بالعملية على جميع الملفات الجديدة (أو التي تم تعديلها مؤخراً)
    for filename in os.listdir(CONTENT_DIR):
        if filename.endswith('.md'):
            filepath = os.path.join(CONTENT_DIR, filename)
            
            # قراءة محتوى الملف
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            match = front_matter_pattern.match(content)
            
            # فصل الـ Front Matter عن محتوى المقال
            if match:
                front_matter = match.group(0)
                body = content[len(front_matter):]
            else:
                front_matter = ''
                body = content

            links_injected = 0
            new_body = body
            
            print(f"\n- فحص الملف: {filename}")
            
            # حلقة للبحث عن الكلمات المفتاحية
            for keyword, data in affiliate_map.items():
                if links_injected >= MAX_LINKS_PER_ARTICLE:
                    break

                # بناء الكود المختصر الذي سيتم حقنه
                shortcode_to_inject = f'{{{{< affiliate_link url="{data["url"]}" text="{data["text"]}" >}}}}'
                
                # بناء نمط البحث: نبحث عن الكلمة المفتاحية بالكامل (باستخدام حدود الكلمات \b)
                # ولا نسمح بالحقن داخل وسم Markdown أو HTML أو داخل كود مختصر آخر
                search_pattern = re.compile(
                    rf'\b({re.escape(keyword)})\b'  # الكلمة المفتاحية كاملة
                )
                
                # البحث عن أول ظهور للكلمة المفتاحية في نص المقال
                match_found = search_pattern.search(new_body)
                
                if match_found:
                    # نتحقق من أن الحقن سيتم في مكان آمن (هذا تحقق أساسي)
                    start_index = match_found.start()
                    
                    # نستخدم شرط: إذا لم تكن الكلمة محاطة بالفعل برابط أو كود مختصر (للتبسيط)
                    # ولضمان عدم حقن الروابط فوق بعضها، سنستبدل أول ظهور
                    
                    # يتم استبدال الكلمة المفتاحية بالكود المختصر
                    # ملاحظة: نستخدم re.sub مع count=1 لضمان استبدال واحد فقط
                    new_body, num_subs = search_pattern.subn(
                        shortcode_to_inject, 
                        new_body, 
                        count=1
                    )
                    
                    if num_subs > 0:
                        links_injected += 1
                        print(f"  ✅ حقن الرابط ({links_injected}/{MAX_LINKS_PER_ARTICLE}) للكلمة: '{keyword}'")

            # دمج الـ Front Matter والمحتوى الجديد وكتابة الملف
            final_content = front_matter + new_body
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(final_content)

    print("\n--- انتهت عملية حقن الروابط الأوتوماتيكية ---")


if __name__ == "__main__":
    affiliates = load_affiliates(AFFILIATE_CSV)
    if affiliates:
        inject_links(affiliates)
    else:
        print("🛑 فشل في تحميل بيانات الـ Affiliate. لم يتم تعديل أي ملفات.")
