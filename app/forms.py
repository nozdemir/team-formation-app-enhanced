from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length, Optional
from wtforms.widgets import CheckboxInput, ListWidget

class MultiCheckboxField(SelectMultipleField):
    """Custom field for multiple checkboxes"""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class TeamFormationForm(FlaskForm):
    """Form for team formation configuration"""
    
    algorithm = SelectField(
        'Algorithm',
        choices=[
            ('ACET', 'All-Connections-Equal Team Formation'),
            ('CAT', 'Co-Authorship Team Formation'),
            ('OAT', 'Organizational Affiliation Team Formation'),
            ('PRT', 'Prioritized Relationship Team Formation'),
            ('COT', 'Cohesion-Optimized Team Formation'),
            ('TAT', 'Time-Aware Team Formation'),
            ('CIT', 'Citation-Optimized Team Formation')
        ],
        default='ACET',
        validators=[DataRequired()],
        description='Select the team formation algorithm to use'
    )
    
    keywords = MultiCheckboxField(
        'Keywords',
        choices=[],  # Will be populated dynamically
        validators=[Optional()],
        description='Select expertise areas for team formation'
    )
    
    custom_keywords = TextAreaField(
        'Custom Keywords',
        validators=[Optional(), Length(max=500)],
        description='Enter additional keywords separated by commas (optional)',
        render_kw={"placeholder": "e.g., machine learning, data analysis, optimization"}
    )
    
    max_teams = IntegerField(
        'Maximum Teams',
        default=3,
        validators=[DataRequired(), NumberRange(min=1, max=10)],
        description='Maximum number of teams to generate'
    )
    
    submit = SubmitField('Build Teams')
    
    def validate(self, extra_validators=None):
        """Custom validation"""
        initial_validation = super(TeamFormationForm, self).validate(extra_validators)
        
        if not initial_validation:
            return False
        
        # Check if at least one keyword is selected or custom keywords are provided
        if not self.keywords.data and not self.custom_keywords.data:
            self.keywords.errors.append('Please select at least one keyword or enter custom keywords.')
            return False
        
        return True