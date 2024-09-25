# Generated by Django 3.2.21 on 2023-09-07 17:10

# Django imports
from django.db import migrations

# Third Party
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ("wagtail_parler_tests", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="foodtranslation",
            name="qa",
            field=wagtail.fields.StreamField(
                [
                    (
                        "QaBlock",
                        wagtail.blocks.StructBlock(
                            [("text", wagtail.blocks.TextBlock(label="Question"))], label="QA"
                        ),
                    )
                ],
                blank=True,
                null=True,
                use_json_field=True,
                verbose_name="Some QA",
            ),
        ),
        migrations.AddField(
            model_name="weirdfoodtranslation",
            name="qa",
            field=wagtail.fields.StreamField(
                [
                    (
                        "QaBlock",
                        wagtail.blocks.StructBlock(
                            [("text", wagtail.blocks.TextBlock(label="Question"))], label="QA"
                        ),
                    )
                ],
                blank=True,
                null=True,
                use_json_field=True,
                verbose_name="Some QA",
            ),
        ),
        migrations.AddField(
            model_name="foodwithedithandlertranslation",
            name="qa",
            field=wagtail.fields.StreamField(
                [
                    (
                        "QaBlock",
                        wagtail.blocks.StructBlock(
                            [("text", wagtail.blocks.TextBlock(label="Question"))], label="QA"
                        ),
                    )
                ],
                blank=True,
                null=True,
                use_json_field=True,
                verbose_name="Some QA",
            ),
        ),
        migrations.AddField(
            model_name="foodwithemptyedithandlertranslation",
            name="qa",
            field=wagtail.fields.StreamField(
                [
                    (
                        "QaBlock",
                        wagtail.blocks.StructBlock(
                            [("text", wagtail.blocks.TextBlock(label="Question"))], label="QA"
                        ),
                    )
                ],
                blank=True,
                null=True,
                use_json_field=True,
                verbose_name="Some QA",
            ),
        ),
        migrations.AddField(
            model_name="foodwithpanelsinsidemodeltranslation",
            name="qa",
            field=wagtail.fields.StreamField(
                [
                    (
                        "QaBlock",
                        wagtail.blocks.StructBlock(
                            [("text", wagtail.blocks.TextBlock(label="Question"))], label="QA"
                        ),
                    )
                ],
                blank=True,
                null=True,
                use_json_field=True,
                verbose_name="Some QA",
            ),
        ),
        migrations.AddField(
            model_name="foodwithspecificedithandlertranslation",
            name="qa",
            field=wagtail.fields.StreamField(
                [
                    (
                        "QaBlock",
                        wagtail.blocks.StructBlock(
                            [("text", wagtail.blocks.TextBlock(label="Question"))], label="QA"
                        ),
                    )
                ],
                blank=True,
                null=True,
                use_json_field=True,
                verbose_name="Some QA",
            ),
        ),
    ]
