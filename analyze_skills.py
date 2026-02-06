#!/usr/bin/env python3
"""
Skills Analysis Script for aadishv's GitHub Repositories
Analyzes all repositories to extract programming languages, frameworks, and general areas of expertise.
"""

import json
import re
from collections import defaultdict, Counter
from pathlib import Path

def analyze_repositories():
    """Main function to analyze all repositories and generate skills summary."""
    
    # Repository data (extracted from GitHub API)
    repositories = [
        {
            "name": "template",
            "description": "Simple Vite + React + Convex template with shadcn etc. set up. Exactly what you need for your next AI-powered B2B2C SaaS powered by MCP with UX :D",
            "language": "TypeScript",
            "homepage": "",
            "topics": []
        },
        {
            "name": "ohs-ac-utils", 
            "description": "",
            "language": "TypeScript",
            "homepage": "",
            "topics": []
        },
        {
            "name": "dishpy-example-package",
            "description": "",
            "language": "Python", 
            "homepage": "",
            "topics": []
        },
        {
            "name": "scratchpad",
            "description": "",
            "language": None,
            "homepage": "",
            "topics": []
        },
        {
            "name": "chinese",
            "description": "`chinese`, my worst (and most helpful) Python project ever",
            "language": "Python",
            "homepage": "",
            "topics": []
        },
        {
            "name": "aoc",
            "description": "My Advent of Code solutions.",
            "language": "Python",
            "homepage": "",
            "topics": []
        },
        {
            "name": "zhinese",
            "description": "A little side project, Chinese learning app with all the features I've been praying for.",
            "language": "Swift",
            "homepage": "",
            "topics": []
        },
        {
            "name": "beta",
            "description": "",
            "language": "TypeScript",
            "homepage": "",
            "topics": []
        },
        {
            "name": "lyrix",
            "description": "",
            "language": "TypeScript",
            "homepage": "https://lyrix-eight.vercel.app",
            "topics": []
        },
        {
            "name": "pdf",
            "description": "An experimental (and nowhere near complete) Rust PDF parser",
            "language": "Makefile",
            "homepage": "",
            "topics": []
        },
        {
            "name": "vexcode",
            "description": "",
            "language": "HTML",
            "homepage": "",
            "topics": []
        },
        {
            "name": "aadishv-astro",
            "description": "Attempting to rewrite my website in Astro",
            "language": "JavaScript",
            "homepage": "",
            "topics": []
        },
        {
            "name": "christmas",
            "description": "Fancy christmas cards for my nuclear & visiting family, was a blast to design (with input from my sister!)",
            "language": "CSS",
            "homepage": "",
            "topics": []
        },
        {
            "name": "aadishv.github.io",
            "description": "Aadish Verma's personal website",
            "language": "TypeScript", 
            "homepage": "https://aadishv.github.io/",
            "topics": ["astro", "react", "shadcn-ui", "tailwindcss"]
        },
        {
            "name": "Objects",
            "description": "",
            "language": "Python",
            "homepage": "",
            "topics": []
        },
        {
            "name": "dishpy",
            "description": "Python development tool for the VEX V5 supporting multiple files, any editor, a CLI, and libraries",
            "language": "Python",
            "homepage": "https://aadishv.github.io/dishpy/",
            "topics": []
        },
        {
            "name": "doleofdoves",
            "description": "Winners of the Stanford OHS 2024 Labor Day Hackathon",
            "language": "Python",
            "homepage": "https://doleofdoves.streamlit.app",
            "topics": []
        },
        {
            "name": "JetsonCode",
            "description": "",
            "language": "Python",
            "homepage": "",
            "topics": []
        },
        {
            "name": "HighStakes",
            "description": "Aadish's clone of code",
            "language": "C++",
            "homepage": "",
            "topics": []
        },
        {
            "name": "usaco",
            "description": "my usaco solutions",
            "language": "C++",
            "homepage": "",
            "topics": []
        }
    ]
    
    # Analyze programming languages
    languages = Counter()
    for repo in repositories:
        if repo["language"]:
            languages[repo["language"]] += 1
    
    # Extract frameworks and libraries from descriptions and topics
    frameworks_libraries = set()
    
    # From topics
    for repo in repositories:
        frameworks_libraries.update(repo["topics"])
    
    # From descriptions (extract known frameworks/libraries)
    framework_patterns = {
        "React": r"\breact\b",
        "Vite": r"\bvite\b", 
        "Convex": r"\bconvex\b",
        "shadcn/ui": r"\bshadcn\b",
        "Astro": r"\bastro\b",
        "Streamlit": r"\bstreamlit\b",
        "Swift": r"\bswift\b",
        "Rust": r"\brust\b",
        "MCP": r"\bmcp\b",
        "SaaS": r"\bsaas\b",
        "B2B2C": r"\bb2b2c\b",
        "VEX V5": r"\bvex\s*v5\b",
        "CLI": r"\bcli\b"
    }
    
    for repo in repositories:
        desc = repo["description"].lower() if repo["description"] else ""
        for framework, pattern in framework_patterns.items():
            if re.search(pattern, desc, re.IGNORECASE):
                frameworks_libraries.add(framework)
    
    # Categorize into general areas
    general_areas = {
        "Web Development": [],
        "Mobile Development": [], 
        "Competitive Programming": [],
        "Robotics & Hardware": [],
        "Language Learning Applications": [],
        "Developer Tools": [],
        "AI/ML Applications": [],
        "Educational Projects": [],
        "Personal Projects": []
    }
    
    # Categorize repositories
    for repo in repositories:
        name = repo["name"].lower()
        desc = repo["description"].lower() if repo["description"] else ""
        lang = repo["language"]
        topics = repo["topics"]
        
        # Web Development
        if (lang in ["TypeScript", "JavaScript", "HTML", "CSS"] or 
            any(topic in ["react", "astro", "tailwindcss"] for topic in topics) or
            "website" in desc or "web" in desc or repo["homepage"]):
            general_areas["Web Development"].append(repo["name"])
        
        # Mobile Development  
        if lang == "Swift" or "app" in desc:
            general_areas["Mobile Development"].append(repo["name"])
        
        # Competitive Programming
        if "aoc" in name or "usaco" in name or "advent of code" in desc:
            general_areas["Competitive Programming"].append(repo["name"])
        
        # Robotics & Hardware
        if ("vex" in desc or "jetson" in name.lower() or "robot" in desc or 
            "hardware" in desc or name in ["vexcode", "JetsonCode", "HighStakes"]):
            general_areas["Robotics & Hardware"].append(repo["name"])
        
        # Language Learning
        if "chinese" in name or "chinese" in desc or "learning" in desc:
            general_areas["Language Learning Applications"].append(repo["name"])
        
        # Developer Tools
        if ("tool" in desc or "cli" in desc or "development" in desc or 
            name in ["dishpy", "dishpy-example-package", "ohs-ac-utils"]):
            general_areas["Developer Tools"].append(repo["name"])
        
        # AI/ML Applications  
        if ("ai" in desc or "ml" in desc or "hackathon" in desc or 
            name in ["doleofdoves", "template"]):
            general_areas["AI/ML Applications"].append(repo["name"])
        
        # Educational Projects
        if ("stanford" in desc or "ohs" in desc or "hackathon" in desc or
            "solutions" in desc):
            general_areas["Educational Projects"].append(repo["name"])
        
        # Personal Projects
        if ("personal" in desc or "christmas" in name or "website" in desc or
            name in ["christmas", "aadishv.github.io", "aadishv-astro", "scratchpad"]):
            general_areas["Personal Projects"].append(repo["name"])
    
    return {
        "programming_languages": dict(languages.most_common()),
        "frameworks_libraries": sorted(list(frameworks_libraries)),
        "general_areas": {k: v for k, v in general_areas.items() if v},
        "total_repositories": len(repositories)
    }

def generate_skills_report(analysis):
    """Generate a comprehensive skills report."""
    
    report = f"""# Aadish Verma - Skills Analysis

Based on analysis of {analysis['total_repositories']} GitHub repositories.

## 1. Programming Languages

"""
    
    # Programming languages section
    for i, (lang, count) in enumerate(analysis['programming_languages'].items(), 1):
        percentage = (count / analysis['total_repositories']) * 100
        report += f"{i}. **{lang}** - {count} repositories ({percentage:.1f}%)\n"
    
    report += f"""
## 2. (Meta-)Frameworks & Libraries

"""
    
    # Frameworks and libraries section
    for i, framework in enumerate(analysis['frameworks_libraries'], 1):
        report += f"{i}. {framework}\n"
    
    report += f"""
## 3. General Areas

"""
    
    # General areas section
    for i, (area, repos) in enumerate(analysis['general_areas'].items(), 1):
        report += f"{i}. **{area}** ({len(repos)} repositories)\n"
        for repo in repos:
            report += f"   - {repo}\n"
        report += "\n"
    
    report += f"""
## Summary

Aadish demonstrates expertise across multiple domains:

- **Primary Languages**: {', '.join([lang for lang, _ in list(analysis['programming_languages'].items())[:3]])}
- **Full-Stack Development**: Frontend (React, TypeScript, Astro), Backend (Python), Mobile (Swift)
- **Specialized Tools**: VEX V5 robotics, competitive programming, language learning applications
- **Modern Tech Stack**: Uses contemporary frameworks like Vite, Convex, shadcn/ui, Tailwind CSS
- **Educational Background**: Active in competitive programming (USACO, Advent of Code) and hackathons
- **Open Source**: Maintains developer tools and educational resources

Generated on {Path(__file__).stat().st_mtime} by automated analysis script.
"""
    
    return report

if __name__ == "__main__":
    analysis = analyze_repositories()
    report = generate_skills_report(analysis)
    
    # Save to file
    with open("skills_analysis.md", "w") as f:
        f.write(report)
    
    print("Skills analysis complete! Report saved to skills_analysis.md")
    print("\nQuick Summary:")
    print(f"- {len(analysis['programming_languages'])} programming languages")
    print(f"- {len(analysis['frameworks_libraries'])} frameworks/libraries identified") 
    print(f"- {len(analysis['general_areas'])} general areas of expertise")
    print(f"- {analysis['total_repositories']} total repositories analyzed")