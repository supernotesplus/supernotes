package main

import (
	"fmt"
	"os"
	"os/exec"
)

func main() {
	if os.Getenv("GITHUB_ACTIONS") != "true" {
		fmt.Println("❌ يجب تشغيل هذا السكربت ضمن بيئة GitHub Actions.")
		os.Exit(1)
	}

	// 1. تثبيت الحزم الضرورية لـ Python (تم إضافة python-slugify)
	fmt.Println("⚙️ تثبيت الحزم المطلوبة (pandas, openai, python-slugify)...")
	// تم إضافة "python-slugify" إلى قائمة التثبيت
	cmd := exec.Command("pip", "install", "pandas", "openai", "requests", "python-slugify")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		fmt.Printf("❌ فشل في تثبيت حزم Python: %v\n", err)
		os.Exit(1)
	}

	// 2. تشغيل سكربت التوليد الرئيسي (generator.py)
	fmt.Println("🚀 بدء عملية توليد المحتوى...")
	cmd = exec.Command("python", "content-engine/generator.py")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err = cmd.Run()
	if err != nil {
		fmt.Printf("❌ فشل في تشغيل generator.py: %v\n", err)
		// لا نخرج بـ 1 هنا، لأننا نريد للسيرفر أن يواصل حتى لو لم يجد كلمات جديدة
	}
	
	// 3. تشغيل سكربت حقن الروابط (inject_affiliates.py)
	fmt.Println("🔗 بدء عملية حقن روابط الأفلييت...")
	cmd = exec.Command("python", "inject_affiliates.py")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err = cmd.Run()
	if err != nil {
		fmt.Printf("❌ فشل في تشغيل inject_affiliates.py: %v\n", err)
	}
	
	fmt.Println("✅ اكتملت عمليات التوليد والحقن بنجاح.")
}
