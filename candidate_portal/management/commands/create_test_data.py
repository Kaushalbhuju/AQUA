from django.core.management.base import BaseCommand
from candidate_portal.models import Agent, Candidate

class Command(BaseCommand):
    help = 'Create test agents and candidates'

    def handle(self, *args, **options):
        # Create agent
        agent, created = Agent.objects.get_or_create(
            agent_code="TEST001",
            defaults={
                'name': 'Test Agent',
                'email': 'test@agent.com',
                'promo_code': 'PROMO123',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created test agent: TEST001'))
        
        # Create candidate
        candidate, created = Candidate.objects.get_or_create(
            email='john@example.com',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '1234567890',
                'agent': agent,
                'pincode': '123456',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created test candidate: John Doe (pincode: 123456)'))
        
        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
        self.stdout.write('Login with: Agent Code=TEST001, Pincode=123456')