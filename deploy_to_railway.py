#!/usr/bin/env python3
"""
CardioGenie Railway Deployment Preparation Script
Prepares the codebase for Railway deployment
"""

import os
import shutil
import json

def prepare_deployment():
    """Prepare CardioGenie for Railway deployment"""
    
    print("🚂 Preparing CardioGenie for Railway Deployment...")
    
    # 1. Ensure static directory exists
    static_dir = "backend/static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        print(f"✅ Created {static_dir} directory")
    
    # 2. Copy frontend to static directory
    frontend_file = "frontend/index.html"
    static_file = "backend/static/index.html"
    
    if os.path.exists(frontend_file):
        shutil.copy2(frontend_file, static_file)
        print(f"✅ Copied {frontend_file} to {static_file}")
    else:
        print(f"❌ Frontend file not found: {frontend_file}")
        return False
    
    # 3. Verify railway.json exists
    railway_config = "railway.json"
    if os.path.exists(railway_config):
        print(f"✅ Railway configuration found: {railway_config}")
    else:
        print(f"❌ Railway configuration missing: {railway_config}")
        return False
    
    # 4. Verify requirements.txt
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        print(f"✅ Requirements file found: {requirements_file}")
    else:
        print(f"❌ Requirements file missing: {requirements_file}")
        return False
    
    # 5. Verify medical dataset
    dataset_file = "docs/Datasetab94d2b.json"
    if os.path.exists(dataset_file):
        print(f"✅ Medical dataset found: {dataset_file}")
    else:
        print(f"❌ Medical dataset missing: {dataset_file}")
        return False
    
    # 6. Check database directory
    db_dir = "database"
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"✅ Created {db_dir} directory")
    
    print("\n🎯 Deployment Checklist:")
    print("✅ Static files prepared")
    print("✅ Railway configuration ready")
    print("✅ Dependencies specified")
    print("✅ Medical dataset available")
    print("✅ Database directory ready")
    
    print("\n🚀 Next Steps:")
    print("1. Push your code to GitHub")
    print("2. Go to railway.app and create new project")
    print("3. Connect your GitHub repository")
    print("4. Add environment variables:")
    print("   - GROQ_API_KEY")
    print("   - TELEGRAM_BOT_TOKEN")
    print("   - DOCTOR_CHAT_ID")
    print("   - DOCTOR_EMAIL")
    print("   - GOOGLE_CLIENT_ID")
    print("   - GOOGLE_CLIENT_SECRET")
    print("   - GOOGLE_REDIRECT_URI (update after deployment)")
    print("5. Deploy and test!")
    
    print("\n🏆 Your app will be available at: https://your-app.railway.app")
    
    return True

if __name__ == "__main__":
    success = prepare_deployment()
    if success:
        print("\n✅ Deployment preparation complete!")
    else:
        print("\n❌ Deployment preparation failed!")
        exit(1) 