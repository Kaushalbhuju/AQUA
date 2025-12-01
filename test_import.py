import sys
import os

# Add the project root to Python path
sys.path.append('E:\\Aqua\\rm_system')

try:
    from dashboard.views.agent_views import agent_dashboard
    print("SUCCESS: agent_dashboard imported successfully!")
    print("Function location:", agent_dashboard.__module__)
except ImportError as e:
    print("ERROR: Could not import agent_dashboard")
    print("Error details:", e)
    
    # Let's see what's in the module
    try:
        import dashboard.views.agent_views as agent_views
        print("Available functions in agent_views:")
        for item in dir(agent_views):
            if not item.startswith('_'):
                print(f"  - {item}")
    except Exception as e2:
        print("Couldn't even import the module:", e2)
        