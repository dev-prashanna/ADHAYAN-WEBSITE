"""Bundled illustrative project covers and their attribution."""

PROJECT_COVERS = {
    "transformer-from-scratch": {
        "author": "dvgodoy", "license": "CC BY 4.0",
        "source": "https://commons.wikimedia.org/wiki/File:Transformer,_full_architecture.png",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
    },
    "adhayan-weekly-competition-2": {
        "author": "Josef Steppan", "license": "CC BY-SA 4.0",
        "source": "https://commons.wikimedia.org/wiki/File:MnistExamples.png",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
    },
    "fifa-data-exploration": {
        "author": "Sonja Guina", "license": "CC0",
        "source": "https://commons.wikimedia.org/wiki/File:Soccer_Field_(Unsplash).jpg",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
    },
    "flood-victim-tracking-app": {
        "author": "Wes Warren", "license": "Unsplash License",
        "source": "https://unsplash.com/photos/NvzUyc9VifQ",
        "license_url": "https://unsplash.com/license",
    },
    "yolov11-posture-recognition": {
        "author": "Wesley Tingey", "license": "Unsplash License",
        "source": "https://unsplash.com/photos/zjO7xkCogZM",
        "license_url": "https://unsplash.com/license",
    },
    "healstream-c-effect-aeolian-nexus": {
        "author": "Chris Ried", "license": "Unsplash License",
        "source": "https://unsplash.com/photos/ieic5Tq8YMk",
        "license_url": "https://unsplash.com/license",
    },
    "test-project-alpha": {
        "author": "Unsplash", "license": "Unsplash License",
        "source": "https://images.unsplash.com/photo-1555066931-4365d14bab8c",
        "license_url": "https://unsplash.com/license",
    },
}


def cover_path(slug):
    return f"/static/images/projects/{slug}.webp"


def backfill_project_covers(project_model):
    """Fill blank covers only, leaving images chosen in the CMS intact."""
    changed = 0
    for slug in PROJECT_COVERS:
        project = project_model.query.filter_by(slug=slug).first()
        if project is not None and not project.cover_image:
            project.cover_image = cover_path(slug)
            changed += 1
    return changed
