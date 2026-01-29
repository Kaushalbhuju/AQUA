class SidebarManager {
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.toggleBtn = document.getElementById('sidebarToggle');
        this.overlay = document.getElementById('sidebarOverlay');
        
        this.init();
    }
    
    init() {
        this.toggleBtn.addEventListener('click', () => this.toggleSidebar());
        this.overlay.addEventListener('click', () => this.closeSidebar());
        
        // Close sidebar when clicking nav links on mobile
        if (window.innerWidth < 768) {
            document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
                link.addEventListener('click', () => this.closeSidebar());
            });
        }
        
        // Handle window resize
        window.addEventListener('resize', () => this.handleResize());
    }
    
    toggleSidebar() {
        this.sidebar.classList.toggle('active');
        this.overlay.classList.toggle('active');
    }
    
    closeSidebar() {
        this.sidebar.classList.remove('active');
        this.overlay.classList.remove('active');
    }
    
    handleResize() {
        if (window.innerWidth >= 768) {
            this.closeSidebar();
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SidebarManager();
});