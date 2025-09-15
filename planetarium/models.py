import os
import uuid

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class PlanetariumDome(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class ShowTheme(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class AstronomyShow(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    theme = models.ForeignKey(
        ShowTheme,
        on_delete=models.SET_NULL,
        null=True,
        related_name="astronomy_shows"
    )

    def __str__(self):
        return self.title


class ShowSession(models.Model):
    show_time = models.DateTimeField()
    astronomy_show = models.ForeignKey(
        AstronomyShow,
        on_delete=models.CASCADE,
        related_name="show_sessions"
    )
    planetarium_dome = models.ForeignKey(
        PlanetariumDome,
        on_delete=models.CASCADE,
        related_name="show_sessions"
    )

    class Meta:
        ordering = ["-show_time"]

    def __str__(self):
        return f"{self.astronomy_show.title} @ {self.show_time}"


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reservation by {self.user.email} on {self.created_at}"


class Ticket(models.Model):
    show_session = models.ForeignKey(
        ShowSession,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    row = models.IntegerField()
    seat = models.IntegerField()

    @staticmethod
    def validate_ticket(row, seat, dome, error_to_raise):
        for value, name, dome_attr in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            max_value = getattr(dome, dome_attr)
            if not (1 <= value <= max_value):
                raise error_to_raise({
                    name: f"{name} must be in range (1, {max_value})"
                })

    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.show_session.planetarium_dome,
            ValidationError
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.show_session} [Row {self.row}, Seat {self.seat}]"

    class Meta:
        unique_together = ("show_session", "row", "seat")
        ordering = ["row", "seat"]
