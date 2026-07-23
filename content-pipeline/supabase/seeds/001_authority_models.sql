-- Created: 2026-07-23 11:07 AM
-- Last edited: 2026-07-23 11:07 AM
-- Seed data: Authority models for source validation

INSERT INTO authority_models (
  industry_key,
  name,
  description,
  max_retry_attempts,
  min_valid_sources,
  retry_strategies,
  strategy_queries,
  relevance_keywords,
  fallback_primary,
  fallback_secondary,
  allowed_claims,
  disallowed_claims,
  repositioning_rules,
  authority_phrase,
  authority_examples,
  notes
) VALUES
(
  'home_services',
  'Home Services (Plumbing, Roofing, HVAC, General Contracting)',
  'Home repair and maintenance services. Min sources can be zero—expert content is primary authority. Trade standards are acceptable sources.',
  6,
  0,
  ARRAY[
    'trade_associations',
    'manufacturer_specifications',
    'building_codes',
    'industry_forums',
    'textbooks_trade',
    'government_building_databases'
  ],
  '{"trade_associations": "site:nrca.net OR site:phccweb.org OR site:acca.com {topic}", "manufacturer_specifications": "{topic} manufacturer specifications installation guide", "building_codes": "{topic} IPC IRC building code requirements", "industry_forums": "{topic} professional contractor forum discussion", "textbooks_trade": "{topic} trade certification textbook", "government_building_databases": "{topic} site:energy.gov OR site:hud.gov"}'::jsonb,
  ARRAY['roof', 'roofing', 'hvac', 'plumbing', 'installation', 'contractor', 'ventilation', 'shingle', 'insulation', 'maintenance', 'repair', 'building', 'code', 'warranty', 'durability', 'weather', 'hail', 'wind'],
  'FIELD_EXPERTISE',
  ARRAY['MANUFACTURER_DATA', 'INDUSTRY_STANDARDS'],
  ARRAY['installation_procedures', 'material_properties', 'cost_factors', 'troubleshooting', 'maintenance_schedules', 'equipment_selection'],
  ARRAY['health_claims_without_source', 'compliance_without_code_reference', 'energy_savings_percentages', 'regulatory_requirements'],
  '[
    {"pattern": "Industry standards require...", "replacement": "In our experience, best practice is...", "context": "For standard-based claims", "sort_order": 1},
    {"pattern": "Research shows...", "replacement": "We'"'"'ve found that...", "context": "For general claims", "sort_order": 2},
    {"pattern": "Studies indicate...", "replacement": "Through years of installations...", "context": "For data-based claims", "sort_order": 3},
    {"pattern": "[EQUIPMENT] reduces costs by [X]%", "replacement": "[EQUIPMENT] typically reduces costs", "context": "Avoid specific percentages without source", "sort_order": 4}
  ]'::jsonb,
  'Based on [X] years of professional installation and service',
  ARRAY['Drawing on our team'"'"'s 40+ years combined experience', 'From thousands of installations we'"'"'ve completed', 'Based on daily work in the field'],
  'Home services content is highly practical. min_valid_sources_required is zero because field expertise is the primary authority. External sources are nice-to-have but not required. Always reference building codes when applicable.'
),
(
  'health_wellness_spa',
  'Health, Wellness & Spa Services',
  'Wellness services including massage therapy, spa treatments, hydrotherapy, fitness coaching, and other therapeutic modalities. Requires at least one verified wellness-focused source.',
  6,
  1,
  ARRAY[
    'peer_reviewed_medical',
    'professional_associations_massage_therapy',
    'wellness_institutes',
    'government_health_databases',
    'textbooks_continuing_education',
    'grey_literature_clinical_reports'
  ],
  '{"peer_reviewed_medical": "{topic} site:ncbi.nlm.nih.gov OR site:pubmed.ncbi.nlm.nih.gov", "professional_associations_massage_therapy": "AMTA OR NBCTMB {topic}", "wellness_institutes": "{topic} Global Wellness Institute", "government_health_databases": "{topic} site:cdc.gov OR site:nih.gov", "textbooks_continuing_education": "{topic} massage therapy textbook education", "grey_literature_clinical_reports": "{topic} spa clinic wellness study"}'::jsonb,
  ARRAY['wellness', 'spa', 'massage', 'therapy', 'hydrotherapy', 'relaxation', 'stress', 'muscle', 'circulation', 'tension', 'recovery', 'self-care', 'treatment', 'therapeutic', 'client', 'practitioner'],
  'PRACTITIONER_EXPERTISE',
  ARRAY['CLIENT_OBSERVATION', 'INDUSTRY_STANDARDS'],
  ARRAY['client_outcomes', 'mechanism_of_action', 'comparison_to_alternatives', 'safety_protocols', 'therapist_observations'],
  ARRAY['specific_percentages_without_source', 'disease_treatment_claims', 'medical_efficacy_claims', 'pharmaceutical_comparisons'],
  '[
    {"pattern": "Research shows that...", "replacement": "Our therapists observe that...", "context": "For general research claims", "sort_order": 1},
    {"pattern": "Studies indicate...", "replacement": "In our practice, we'"'"'ve found that...", "context": "For claims based on studies", "sort_order": 2},
    {"pattern": "[PERCENTAGE]% improvement...", "replacement": "Clients frequently report...", "context": "For specific statistics", "sort_order": 3},
    {"pattern": "According to [WELLNESS_ORG]...", "replacement": "Industry best practices recognize...", "context": "For organizational citations", "sort_order": 4}
  ]'::jsonb,
  'Based on direct work with hundreds of clients',
  ARRAY['Based on our experience with 500+ clients', 'Drawing on our therapists'" '"'collective expertise', 'From thousands of sessions we'"'"'ve facilitated'],
  'Health/wellness content must avoid medical claims that require peer-reviewed sources. When sources fail, repositioning under practitioner expertise is highly credible for wellness content.'
),
(
  'software_development',
  'Software Development & Technology',
  'Software development, programming, DevOps, technical architecture. Min 1 source acceptable. Developer experience is highly valued authority.',
  6,
  1,
  ARRAY[
    'official_documentation',
    'peer_reviewed_technical',
    'established_tech_publications',
    'framework_maintainers',
    'industry_best_practices',
    'technical_community'
  ],
  '{"official_documentation": "{topic} site:github.com OR site:docs.", "peer_reviewed_technical": "{topic} IEEE OR ACM", "established_tech_publications": "{topic} TechCrunch OR Verge", "framework_maintainers": "{topic} GitHub official blog", "industry_best_practices": "{topic} RFC standard", "technical_community": "{topic} Stack Overflow"}'::jsonb,
  ARRAY['api', 'software', 'development', 'framework', 'library', 'deployment', 'security', 'performance', 'architecture', 'database', 'cloud', 'devops', 'testing', 'code', 'programming', 'runtime', 'version'],
  'DEVELOPER_EXPERTISE',
  ARRAY['OPEN_SOURCE_COMMUNITY', 'INDUSTRY_STANDARDS'],
  ARRAY['implementation_patterns', 'performance_considerations', 'code_organization', 'debugging_approaches', 'best_practices', 'technology_comparisons'],
  ARRAY['security_vulnerabilities_without_proof', 'specific_performance_metrics', 'compliance_certifications', 'licensing_requirements'],
  '[
    {"pattern": "Research shows...", "replacement": "We'"'"'ve found in practice...", "context": "For technical research", "sort_order": 1},
    {"pattern": "Studies indicate...", "replacement": "Experience shows...", "context": "For technical data", "sort_order": 2},
    {"pattern": "[FRAMEWORK] reduces development time by [X]%", "replacement": "[FRAMEWORK] typically accelerates development", "context": "For performance claims", "sort_order": 3},
    {"pattern": "According to [ORG]...", "replacement": "In the developer community...", "context": "For organizational citations", "sort_order": 4}
  ]'::jsonb,
  'Based on [X] years of software development experience',
  ARRAY['Drawing on our team'"'"'s combined 100+ years of coding', 'From thousands of lines of code we'"'"'ve written', 'Based on production systems we'"'"'ve built and maintained'],
  'Software/tech content thrives on developer expertise and open source community perspective. Official documentation is the gold standard source. Security claims require proof—don'"'"'t claim vulnerabilities without CVE or proof-of-concept.'
),
(
  'financial_advisory',
  'Financial Advisory & Insurance',
  'Financial planning, investment advice, insurance guidance. Requires 2 verified regulatory or institutional sources. Highly restricted fallback.',
  6,
  2,
  ARRAY[
    'regulatory_sources',
    'financial_institutions',
    'certified_advisor_associations',
    'government_financial_databases',
    'industry_research',
    'textbooks_finance'
  ],
  '{"regulatory_sources": "{topic} site:sec.gov OR site:finra.org OR site:cfpb.gov", "financial_institutions": "{topic} site:federalreserve.gov", "certified_advisor_associations": "{topic} CFP Board OR NAPFA OR CFA", "government_financial_databases": "{topic} site:irs.gov OR site:treasury.gov", "industry_research": "{topic} financial research report", "textbooks_finance": "{topic} finance textbook certification"}'::jsonb,
  ARRAY['investment', 'retirement', 'portfolio', 'insurance', 'tax', 'regulation', 'sec', 'finra', 'cfpb', 'interest', 'rate', 'risk', 'savings', 'planning', 'advisor', 'fiduciary', 'compliance', 'market'],
  'ADVISOR_EXPERTISE',
  ARRAY['REGULATORY_FRAMEWORK', 'INDUSTRY_STANDARDS'],
  ARRAY['planning_process_overview', 'general_financial_concepts', 'question_framework', 'advisor_perspective'],
  ARRAY['specific_investment_recommendations', 'rate_or_return_projections', 'regulatory_interpretation', 'compliance_requirements', 'tax_advice'],
  '[
    {"pattern": "The SEC requires...", "replacement": "Generally, regulatory requirements include...", "context": "For regulatory claims", "sort_order": 1},
    {"pattern": "Historical data shows [X]% returns...", "replacement": "Markets have historically shown variability...", "context": "Avoid specific return projections", "sort_order": 2},
    {"pattern": "Studies indicate that...", "replacement": "Many advisors recommend...", "context": "For research-based claims", "sort_order": 3},
    {"pattern": "You should...", "replacement": "Many clients find it helpful to...", "context": "Avoid direct recommendations", "sort_order": 4}
  ]'::jsonb,
  'Based on [X] years of financial advisory experience',
  ARRAY['In our practice advising hundreds of clients', 'Drawing on our team'"'"'s combined experience', 'Based on conversations with clients in this situation'],
  'Financial advice carries significant legal/liability concerns. Fallback mode is restricted to general concepts only. Specific investment advice, returns projections, and regulatory interpretation MUST have sources. Consider requiring 3-4 sources for investment-focused content.'
),
(
  'legal_services',
  'Legal Services & Law Firms',
  'Legal practice, law firms, and legal education. Requires at least 3 verified legal sources to proceed. Heavily restricted fallback mode.',
  6,
  3,
  ARRAY[
    'primary_legal_sources',
    'case_law_databases',
    'bar_association_publications',
    'law_review_articles',
    'government_statutes',
    'legal_textbooks'
  ],
  '{"primary_legal_sources": "{topic} site:law.cornell.edu OR site:justia.com", "case_law_databases": "{topic} case law Google Scholar", "bar_association_publications": "{topic} site:americanbar.org", "law_review_articles": "{topic} law review journal", "government_statutes": "{topic} site:congress.gov", "legal_textbooks": "{topic} legal textbook education"}'::jsonb,
  ARRAY['statute', 'regulation', 'court', 'case', 'law', 'legal', 'attorney', 'liability', 'compliance', 'precedent', 'plaintiff', 'defendant', 'contract', 'claim', 'damages', 'jurisdiction'],
  'ATTORNEY_EXPERTISE',
  ARRAY['CASE_PRECEDENT', 'STATUTORY_FRAMEWORK'],
  ARRAY['legal_process_explanation', 'common_scenarios', 'risk_assessment', 'strategic_considerations', 'attorney_perspective'],
  ARRAY['specific_precedent_without_citation', 'legal_advice_for_specific_case', 'guaranteed_outcomes', 'statutory_interpretation', 'regulatory_compliance'],
  '[
    {"pattern": "Legal precedent establishes...", "replacement": "In our experience with similar cases...", "context": "For precedent-based claims", "sort_order": 1},
    {"pattern": "The statute requires...", "replacement": "Generally, the law addresses...", "context": "For statutory interpretation", "sort_order": 2},
    {"pattern": "[COURT] decided that...", "replacement": "Courts have generally found...", "context": "For specific case citations", "sort_order": 3},
    {"pattern": "This guarantees...", "replacement": "This typically results in...", "context": "Avoid absolute guarantees", "sort_order": 4}
  ]'::jsonb,
  'Based on [X] years of legal practice',
  ARRAY['Drawing on our firm'"'"'s 25 years of experience', 'From our perspective as practicing attorneys', 'Based on patterns we'"'"'ve observed in practice'],
  'Legal content carries significant liability. Fallback mode is restricted—only general legal process can be explained under attorney authority. Specific legal advice requires sources. Consider requiring 5 sources for high-liability practice areas.'
);
