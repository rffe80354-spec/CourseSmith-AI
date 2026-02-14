"""
Product Templates Module - Defines digital product types for CourseSmith AI.
Implements a scalable template system for different product types:
- Mini Course
- Lead Magnet
- Paid Guide
- 30-Day Challenge
- Checklist
- Full Course (default)

Each template defines:
- Structure (chapter count, content length)
- Credit cost
- Prompts for generation
- Export metadata
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class ProductTemplate:
    """
    Data class representing a product template configuration.
    
    Attributes:
        id: Unique identifier for the template
        name: Display name for the template
        description: Brief description of the product type
        chapter_count: Number of chapters/sections to generate
        chars_per_chapter: Target character count per chapter
        credit_cost: Number of credits required to generate
        structure_prompt: System prompt for structure generation
        content_prompt: System prompt for content generation
        icon: Emoji icon for UI display
    """
    id: str
    name: str
    description: str
    chapter_count: int
    chars_per_chapter: int
    credit_cost: int
    structure_prompt_en: str
    structure_prompt_ru: str
    content_prompt_en: str
    content_prompt_ru: str
    icon: str = "📄"
    tags: List[str] = field(default_factory=list)


# ============================================================================
# TEMPLATE DEFINITIONS
# ============================================================================

MINI_COURSE = ProductTemplate(
    id="mini_course",
    name="Mini Course",
    description="A concise 5-chapter course for quick learning",
    chapter_count=5,
    chars_per_chapter=1000,
    credit_cost=1,
    icon="📚",
    tags=["course", "educational", "quick"],
    structure_prompt_en="""You are an expert at creating focused mini-courses.
Create a structure of EXACTLY 5 chapters for a mini-course.
The chapters should cover the essential concepts concisely.
Focus on practical, actionable content that can be consumed quickly.""",
    structure_prompt_ru="""Вы эксперт по созданию сфокусированных мини-курсов.
Создайте структуру из РОВНО 5 глав для мини-курса.
Главы должны кратко охватывать основные концепции.
Сосредоточьтесь на практическом, применимом контенте.""",
    content_prompt_en="""Write focused, practical content for this mini-course chapter.
Keep it concise (~1000 characters) but valuable.
Include actionable tips and key takeaways.
Use clear, direct language suitable for quick learning.""",
    content_prompt_ru="""Напишите сфокусированный, практический контент для этой главы мини-курса.
Будьте краткими (~1000 символов), но ценными.
Включите практические советы и ключевые выводы.
Используйте ясный, прямой язык для быстрого обучения."""
)

LEAD_MAGNET = ProductTemplate(
    id="lead_magnet",
    name="Lead Magnet",
    description="A 3-section guide perfect for email opt-ins",
    chapter_count=3,
    chars_per_chapter=800,
    credit_cost=1,
    icon="🧲",
    tags=["marketing", "lead-gen", "short"],
    structure_prompt_en="""You are an expert at creating compelling lead magnets.
Create a structure of EXACTLY 3 sections for a lead magnet PDF.
The structure should:
1. Hook the reader with a compelling problem/solution intro
2. Deliver high-value content that demonstrates expertise
3. End with actionable next steps and a soft call-to-action
Focus on creating irresistible value that makes readers want more.""",
    structure_prompt_ru="""Вы эксперт по созданию убедительных лид-магнитов.
Создайте структуру из РОВНО 3 разделов для PDF лид-магнита.
Структура должна:
1. Зацепить читателя убедительным введением
2. Предоставить высокоценный контент, демонстрирующий экспертизу
3. Завершиться практическими шагами и мягким призывом к действию
Создайте неотразимую ценность.""",
    content_prompt_en="""Write compelling lead magnet content that hooks the reader.
Keep it concise (~800 characters) but packed with value.
Focus on one key insight or technique per section.
Make the reader want to learn more from you.""",
    content_prompt_ru="""Напишите убедительный контент лид-магнита, который захватывает читателя.
Будьте краткими (~800 символов), но наполненными ценностью.
Сосредоточьтесь на одном ключевом инсайте на раздел.
Заставьте читателя хотеть узнать больше."""
)

PAID_GUIDE = ProductTemplate(
    id="paid_guide",
    name="Paid Guide",
    description="A comprehensive 12-chapter premium guide",
    chapter_count=12,
    chars_per_chapter=2000,
    credit_cost=2,
    icon="💰",
    tags=["premium", "comprehensive", "detailed"],
    structure_prompt_en="""You are an expert at creating premium educational guides.
Create a structure of EXACTLY 12 chapters for a comprehensive paid guide.
The structure should:
- Start with foundational concepts
- Progress through intermediate techniques
- Culminate in advanced strategies
- Include practical implementation chapters
Each chapter should justify the premium price with depth and value.""",
    structure_prompt_ru="""Вы эксперт по созданию премиальных образовательных руководств.
Создайте структуру из РОВНО 12 глав для комплексного платного руководства.
Структура должна:
- Начинаться с фундаментальных концепций
- Переходить к промежуточным техникам
- Завершаться продвинутыми стратегиями
- Включать главы практической реализации
Каждая глава должна оправдывать премиальную цену глубиной и ценностью.""",
    content_prompt_en="""Write comprehensive, premium-quality educational content.
Target approximately 2000 characters with in-depth explanations.
Include detailed examples, case studies, and expert insights.
Make the content worth paying for - thorough, professional, actionable.""",
    content_prompt_ru="""Напишите комплексный, премиального качества образовательный контент.
Целевой объем ~2000 символов с глубокими объяснениями.
Включите детальные примеры, кейсы и экспертные инсайты.
Сделайте контент стоящим оплаты - тщательным, профессиональным, практичным."""
)

CHALLENGE_30_DAY = ProductTemplate(
    id="30_day_challenge",
    name="30-Day Challenge",
    description="A day-by-day transformation program",
    chapter_count=30,
    chars_per_chapter=500,
    credit_cost=2,
    icon="🏆",
    tags=["challenge", "daily", "transformation"],
    structure_prompt_en="""You are an expert at creating engaging 30-day challenge programs.
Create a structure of EXACTLY 30 daily tasks/lessons for a transformation challenge.
Each day should:
- Have a clear, specific task or focus
- Build progressively on previous days
- Be achievable in 15-30 minutes
- Keep participants motivated and engaged
Structure the challenge with weekly themes for progression.""",
    structure_prompt_ru="""Вы эксперт по созданию увлекательных 30-дневных челленджей.
Создайте структуру из РОВНО 30 ежедневных заданий для трансформационного челленджа.
Каждый день должен:
- Иметь четкую, конкретную задачу
- Прогрессивно строиться на предыдущих днях
- Быть выполнимым за 15-30 минут
- Поддерживать мотивацию участников
Структурируйте челлендж с еженедельными темами.""",
    content_prompt_en="""Write a focused daily challenge task.
Keep it brief (~500 characters) but actionable.
Include: Today's task, why it matters, and how to do it.
Make each day feel achievable yet meaningful.""",
    content_prompt_ru="""Напишите сфокусированное ежедневное задание челленджа.
Будьте краткими (~500 символов), но практичными.
Включите: задание дня, почему это важно, как выполнить.
Сделайте каждый день достижимым, но значимым."""
)

CHECKLIST = ProductTemplate(
    id="checklist",
    name="Checklist",
    description="A practical step-by-step checklist guide",
    chapter_count=5,
    chars_per_chapter=600,
    credit_cost=1,
    icon="✅",
    tags=["checklist", "practical", "actionable"],
    structure_prompt_en="""You are an expert at creating actionable checklists.
Create a structure of EXACTLY 5 checklist sections.
Each section should represent a major phase or category.
Focus on practical, step-by-step guidance that users can follow and check off.""",
    structure_prompt_ru="""Вы эксперт по созданию практических чеклистов.
Создайте структуру из РОВНО 5 разделов чеклиста.
Каждый раздел должен представлять основную фазу или категорию.
Сосредоточьтесь на практическом пошаговом руководстве.""",
    content_prompt_en="""Write a checklist section with clear, actionable items.
Keep it concise (~600 characters) with bullet points.
Format as a numbered or bulleted checklist.
Each item should be specific and completable.""",
    content_prompt_ru="""Напишите раздел чеклиста с четкими, выполнимыми пунктами.
Будьте краткими (~600 символов) с маркированными пунктами.
Оформите как нумерованный или маркированный чеклист.
Каждый пункт должен быть конкретным и выполнимым."""
)

FULL_COURSE = ProductTemplate(
    id="full_course",
    name="Full Course",
    description="A complete 10-chapter professional course",
    chapter_count=10,
    chars_per_chapter=1500,
    credit_cost=3,
    icon="🎓",
    tags=["course", "comprehensive", "professional"],
    structure_prompt_en="""You are an expert at structuring educational courses.
Create a structure of EXACTLY 10 chapters for a comprehensive course.
Requirements:
- Exactly 10 chapters
- Logical progression from basics to advanced topics
- Each title must be professional and informative
- Chapters should sequentially develop the topic""",
    structure_prompt_ru="""Вы эксперт по разработке структуры образовательных курсов.
Создайте структуру из РОВНО 10 глав для образовательного курса.
Требования:
- Ровно 10 глав
- Логическая прогрессия от основ к продвинутым темам
- Каждое название должно быть профессиональным и информативным
- Главы должны последовательно раскрывать тему""",
    content_prompt_en="""Write expert-level educational content.
Target approximately 1500 characters (250-300 words).
Use subheaders (## for sections) to structure the content.
Include bullet points where appropriate.
Professional, expert-level language with practical examples.""",
    content_prompt_ru="""Напишите экспертный образовательный контент.
Целевой объем ~1500 символов (250-300 слов).
Используйте подзаголовки (## для разделов) для структурирования.
Включите маркированные списки где уместно.
Профессиональный, экспертный язык с практическими примерами."""
)


# ============================================================================
# TEMPLATE REGISTRY
# ============================================================================

class ProductTemplateRegistry:
    """
    Registry for managing and accessing product templates.
    Provides a centralized way to register and retrieve templates.
    """
    
    _templates: Dict[str, ProductTemplate] = {}
    
    @classmethod
    def register(cls, template: ProductTemplate) -> None:
        """Register a product template."""
        cls._templates[template.id] = template
    
    @classmethod
    def get(cls, template_id: str) -> Optional[ProductTemplate]:
        """Get a template by ID."""
        return cls._templates.get(template_id)
    
    @classmethod
    def get_all(cls) -> List[ProductTemplate]:
        """Get all registered templates."""
        return list(cls._templates.values())
    
    @classmethod
    def get_by_tag(cls, tag: str) -> List[ProductTemplate]:
        """Get templates that have a specific tag."""
        return [t for t in cls._templates.values() if tag in t.tags]
    
    @classmethod
    def get_ids(cls) -> List[str]:
        """Get all template IDs."""
        return list(cls._templates.keys())
    
    @classmethod
    def get_credit_cost(cls, template_id: str) -> int:
        """Get the credit cost for a template."""
        template = cls.get(template_id)
        return template.credit_cost if template else 1


# Register default templates
ProductTemplateRegistry.register(MINI_COURSE)
ProductTemplateRegistry.register(LEAD_MAGNET)
ProductTemplateRegistry.register(PAID_GUIDE)
ProductTemplateRegistry.register(CHALLENGE_30_DAY)
ProductTemplateRegistry.register(CHECKLIST)
ProductTemplateRegistry.register(FULL_COURSE)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_template(template_id: str) -> Optional[ProductTemplate]:
    """
    Get a product template by ID.
    
    Args:
        template_id: The template identifier.
        
    Returns:
        ProductTemplate or None if not found.
    """
    return ProductTemplateRegistry.get(template_id)


def get_all_templates() -> List[ProductTemplate]:
    """
    Get all available product templates.
    
    Returns:
        List of all ProductTemplate objects.
    """
    return ProductTemplateRegistry.get_all()


def get_template_ids() -> List[str]:
    """
    Get all available template IDs.
    
    Returns:
        List of template ID strings.
    """
    return ProductTemplateRegistry.get_ids()


def get_credit_cost(template_id: str) -> int:
    """
    Get the credit cost for generating a product.
    
    Args:
        template_id: The template identifier.
        
    Returns:
        int: Number of credits required.
    """
    return ProductTemplateRegistry.get_credit_cost(template_id)


def get_structure_prompt(template_id: str, language: str = 'en') -> str:
    """
    Get the structure generation prompt for a template.
    
    Args:
        template_id: The template identifier.
        language: 'en' for English, 'ru' for Russian.
        
    Returns:
        str: The structure prompt.
    """
    template = get_template(template_id)
    if not template:
        template = FULL_COURSE
    
    if language == 'ru':
        return template.structure_prompt_ru
    return template.structure_prompt_en


def get_content_prompt(template_id: str, language: str = 'en') -> str:
    """
    Get the content generation prompt for a template.
    
    Args:
        template_id: The template identifier.
        language: 'en' for English, 'ru' for Russian.
        
    Returns:
        str: The content prompt.
    """
    template = get_template(template_id)
    if not template:
        template = FULL_COURSE
    
    if language == 'ru':
        return template.content_prompt_ru
    return template.content_prompt_en


def get_template_info_for_ui() -> List[Dict]:
    """
    Get template information formatted for UI display.
    
    Returns:
        List of dicts with template info for UI.
    """
    templates = get_all_templates()
    return [
        {
            'id': t.id,
            'name': t.name,
            'description': t.description,
            'icon': t.icon,
            'chapters': t.chapter_count,
            'credits': t.credit_cost
        }
        for t in templates
    ]
