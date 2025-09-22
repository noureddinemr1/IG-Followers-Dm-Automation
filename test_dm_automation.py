#!/usr/bin/env python3
"""
DM Automation Test Script
Tests the DM automation functionality without requiring Instagram credentials
"""

import sys
import json
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from dm_automation import DMAutomation, DMTemplate, DMCampaign

class MockAuth:
    """Mock authentication for testing"""
    def __init__(self):
        self.username = "test_user"
        self.logged_in = True
    
    def get_loader(self):
        return MockLoader()

class MockLoader:
    """Mock instaloader for testing"""
    def __init__(self):
        self.context = MockContext()

class MockContext:
    """Mock context for testing"""
    pass

def test_dm_automation():
    """Test DM automation functionality"""
    print("🧪 Testing DM Automation System")
    print("=" * 50)
    
    # Initialize with mock auth
    auth = MockAuth()
    dm_automation = DMAutomation(auth, data_dir="test_data")
    
    print(f"✅ DM Automation initialized")
    
    # Test template creation
    print("\n📝 Testing Template Creation...")
    template_id = dm_automation.create_template(
        name="Test Template",
        subject="Test Subject",
        message="Hello {username}! This is a test message.",
        variables=["username"]
    )
    print(f"✅ Template created: {template_id}")
    
    # Test template rendering
    template = dm_automation.templates[template_id]
    rendered = template.render(username="test_user")
    print(f"✅ Template rendered: {rendered}")
    
    # Test campaign creation
    print("\n🎯 Testing Campaign Creation...")
    targets = ["user1", "user2", "user3", "user4", "user5"]
    campaign_id = dm_automation.create_campaign(
        name="Test Campaign",
        template_id=template_id,
        target_list=targets
    )
    print(f"✅ Campaign created: {campaign_id}")
    
    # Test campaign start
    print("\n🚀 Testing Campaign Start...")
    start_result = dm_automation.start_campaign(campaign_id)
    print(f"✅ Campaign started: {start_result}")
    
    # Test campaign stats
    print("\n📊 Testing Campaign Stats...")
    stats = dm_automation.get_campaign_stats(campaign_id)
    print(f"✅ Campaign stats: {json.dumps(stats, indent=2)}")
    
    # Test DM stats
    print("\n📈 Testing DM Stats...")
    dm_stats = dm_automation.get_dm_stats()
    print(f"✅ DM stats: {json.dumps(dm_stats, indent=2)}")
    
    # Test rate limiting check
    print("\n⏱️ Testing Rate Limiting...")
    can_send, reason = dm_automation.can_send_dm()
    print(f"✅ Rate limit check: {can_send} - {reason}")
    
    # Test single DM (simulation)
    print("\n📨 Testing Single DM...")
    dm_result = dm_automation.send_dm("test_user", "Test message")
    print(f"✅ DM result: {json.dumps(dm_result, indent=2)}")
    
    # Test campaign run (simulation)
    print("\n🔄 Testing Campaign Run...")
    run_result = dm_automation.run_campaign(campaign_id, max_messages=3)
    print(f"✅ Campaign run result: {json.dumps(run_result, indent=2)}")
    
    # Test blocked users
    print("\n🚫 Testing Blocked Users...")
    dm_automation.block_user("spam_user")
    dm_automation.block_user("another_spam_user")
    print(f"✅ Blocked users: {list(dm_automation.blocked_users)}")
    
    # Test template listing
    print("\n📋 Testing Template Listing...")
    print(f"✅ Total templates: {len(dm_automation.templates)}")
    for template in dm_automation.templates.values():
        print(f"   - {template.name} ({template.id})")
    
    # Test campaign listing
    print("\n📋 Testing Campaign Listing...")
    print(f"✅ Total campaigns: {len(dm_automation.campaigns)}")
    for campaign in dm_automation.campaigns.values():
        print(f"   - {campaign.name} ({campaign.status}) - {len(campaign.target_list)} targets")
    
    print(f"\n🎉 All tests completed successfully!")
    print(f"Test data stored in: test_data/")

def cleanup_test_data():
    """Clean up test data files"""
    import shutil
    test_dir = Path("test_data")
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print(f"🧹 Cleaned up test data directory")

if __name__ == "__main__":
    try:
        test_dm_automation()
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Ask if user wants to keep test data
        response = input("\nKeep test data? (y/n): ").strip().lower()
        if response != 'y':
            cleanup_test_data()