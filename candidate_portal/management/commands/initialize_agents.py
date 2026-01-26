from django.core.management.base import BaseCommand
from candidate_portal.models import Agent

class Command(BaseCommand):
    help = 'Initialize agents with unique codes and pin codes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of agents to initialize'
        )
        parser.add_argument(
            '--max-candidates',
            type=int,
            default=50,
            help='Maximum candidates per agent'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        max_candidates = options['max_candidates']
        
        created_count = 0
        
        for i in range(count):
            agent_code = Agent.generate_agent_code()
            pin_code = Agent.generate_pin_code()
            
            agent, created = Agent.objects.get_or_create(
                agent_code=agent_code,
                defaults={
                    'name': f'Agent {i+1}',
                    'email': f'agent{i+1}@example.com',
                    'pin_code': pin_code,
                    'max_candidates': max_candidates,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created Agent: {agent.agent_code} | '
                        f'Pin Code: {agent.pin_code} | '
                        f'Max Candidates: {agent.max_candidates}'
                    )
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'Agent already exists: {agent.agent_code}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized {created_count} agents. '
                f'Use these credentials for testing.'
            )
        )