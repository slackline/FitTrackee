from datetime import datetime

import pytest
from flask import Flask
from freezegun import freeze_time

from fittrackee import db
from fittrackee.administration.models import AdminAction
from fittrackee.privacy_levels import PrivacyLevel
from fittrackee.reports.exceptions import (
    InvalidReporterException,
    InvalidReportException,
    ReportCommentForbiddenException,
    ReportForbiddenException,
)
from fittrackee.reports.models import Report, ReportComment
from fittrackee.tests.comments.utils import CommentMixin
from fittrackee.users.models import FollowRequest, User
from fittrackee.workouts.models import Sport, Workout

from ..mixins import RandomMixin, UserModerationMixin


class TestReportModel(CommentMixin, RandomMixin):
    def test_it_raises_exception_when_reported_object_is_invalid(
        self, app: Flask, user_1: User, sport_1_cycling: Sport
    ) -> None:
        with pytest.raises(InvalidReportException):
            Report(
                note=self.random_string(),
                reported_by=user_1.id,
                reported_object=sport_1_cycling,
            )

    def test_it_creates_report_for_a_comment(
        self,
        app: Flask,
        user_1: User,
        sport_1_cycling: Sport,
        workout_cycling_user_1: Workout,
        user_2: User,
    ) -> None:
        workout_cycling_user_1.workout_visibility = PrivacyLevel.PUBLIC
        report_created_at = datetime.now()
        report_note = self.random_string()
        comment = self.create_comment(
            user_2, workout_cycling_user_1, text_visibility=PrivacyLevel.PUBLIC
        )

        report = Report(
            created_at=report_created_at,
            note=report_note,
            reported_by=user_1.id,
            reported_object=comment,
        )

        assert report.created_at == report_created_at
        assert report.note == report_note
        assert report.object_type == 'comment'
        assert report.reported_by == user_1.id
        assert report.reported_comment_id == comment.id
        assert report.reported_user_id == user_2.id
        assert report.reported_workout_id is None
        assert report.resolved is False
        assert report.resolved_at is None
        assert report.resolved_by is None
        assert report.updated_at is None

    def test_it_creates_report_for_a_user(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
    ) -> None:
        report_created_at = datetime.now()
        report_note = self.random_string()

        report = Report(
            created_at=report_created_at,
            note=report_note,
            reported_by=user_1.id,
            reported_object=user_2,
        )

        assert report.created_at == report_created_at
        assert report.note == report_note
        assert report.object_type == 'user'
        assert report.reported_by == user_1.id
        assert report.reported_comment_id is None
        assert report.reported_user_id == user_2.id
        assert report.reported_workout_id is None
        assert report.resolved is False
        assert report.resolved_at is None
        assert report.resolved_by is None
        assert report.updated_at is None

    def test_it_creates_report_for_a_workout(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        workout_cycling_user_2.workout_visibility = PrivacyLevel.PUBLIC
        report_created_at = datetime.now()
        report_note = self.random_string()

        report = Report(
            created_at=report_created_at,
            note=report_note,
            reported_by=user_1.id,
            reported_object=workout_cycling_user_2,
        )

        assert report.created_at == report_created_at
        assert report.note == report_note
        assert report.object_type == 'workout'
        assert report.reported_by == user_1.id
        assert report.reported_comment_id is None
        assert report.reported_user_id == user_2.id
        assert report.reported_workout_id == workout_cycling_user_2.id
        assert report.resolved is False
        assert report.resolved_at is None
        assert report.resolved_by is None
        assert report.updated_at is None

    def test_it_creates_report_without_date(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        now = datetime.now()
        report_note = self.random_string()

        with freeze_time(now):
            report = Report(
                note=report_note,
                reported_by=user_1.id,
                reported_object=user_2,
            )

        assert report.created_at == now
        assert report.note == report_note
        assert report.object_type == 'user'
        assert report.reported_by == user_1.id
        assert report.reported_comment_id is None
        assert report.reported_user_id == user_2.id
        assert report.reported_workout_id is None
        assert report.resolved is False
        assert report.resolved_at is None
        assert report.resolved_by is None
        assert report.updated_at is None

    def test_it_raises_exception_when_reported_user_is_reporter(
        self, app: Flask, user_1: User
    ) -> None:
        with pytest.raises(InvalidReporterException):
            Report(
                note=self.random_string(),
                reported_by=user_1.id,
                reported_object=user_1,
            )


class TestReportSerializerAsUser(CommentMixin, RandomMixin):
    def test_it_raises_exception_when_user_is_not_reporter(
        self,
        app: Flask,
        user_1: User,
        sport_1_cycling: Sport,
        workout_cycling_user_1: Workout,
        user_2: User,
        user_3: User,
    ) -> None:
        workout_cycling_user_1.workout_visibility = PrivacyLevel.PUBLIC
        comment = self.create_comment(
            user_2, workout_cycling_user_1, text_visibility=PrivacyLevel.PUBLIC
        )
        report = Report(
            note=self.random_string(),
            reported_by=user_1.id,
            reported_object=comment,
        )
        db.session.add(report)
        db.session.commit()

        with pytest.raises(ReportForbiddenException):
            report.serialize(user_3)

    def test_it_returns_serialized_object_for_comment_report(
        self,
        app: Flask,
        user_1: User,
        sport_1_cycling: Sport,
        workout_cycling_user_1: Workout,
        user_2: User,
    ) -> None:
        workout_cycling_user_1.workout_visibility = PrivacyLevel.PUBLIC
        comment = self.create_comment(
            user_2, workout_cycling_user_1, text_visibility=PrivacyLevel.PUBLIC
        )
        report = Report(
            note=self.random_string(),
            reported_by=user_1.id,
            reported_object=comment,
        )
        db.session.add(report)
        db.session.commit()

        serialized_report = report.serialize(user_1)

        assert serialized_report == {
            "created_at": report.created_at,
            "id": report.id,
            "note": report.note,
            "object_type": "comment",
            "reported_by": user_1.serialize(user_1),
            "reported_comment": comment.serialize(user_1),
            "reported_user": user_2.serialize(),
            "reported_workout": None,
            "resolved": False,
            "resolved_at": None,
        }

    def test_it_returns_serialized_object_report_when_comment_is_not_visible(
        self,
        app: Flask,
        user_1: User,
        sport_1_cycling: Sport,
        workout_cycling_user_1: Workout,
        user_2: User,
    ) -> None:
        # in case visibility changed
        workout_cycling_user_1.workout_visibility = PrivacyLevel.PUBLIC
        comment = self.create_comment(
            user_2, workout_cycling_user_1, text_visibility=PrivacyLevel.PUBLIC
        )
        report = Report(
            note=self.random_string(),
            reported_by=user_1.id,
            reported_object=comment,
        )
        db.session.add(report)
        comment.text_visibility = PrivacyLevel.FOLLOWERS
        db.session.commit()

        serialized_report = report.serialize(user_1)

        assert serialized_report == {
            "created_at": report.created_at,
            "id": report.id,
            "note": report.note,
            "object_type": "comment",
            "reported_by": user_1.serialize(user_1),
            "reported_comment": "_COMMENT_UNAVAILABLE_",
            "reported_user": user_2.serialize(),
            "reported_workout": None,
            "resolved": False,
            "resolved_at": None,
        }

    def test_it_returns_serialized_object_for_user_report(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
    ) -> None:
        report = Report(
            note=self.random_string(),
            reported_by=user_1.id,
            reported_object=user_2,
        )
        db.session.add(report)
        db.session.commit()

        serialized_report = report.serialize(user_1)

        assert serialized_report == {
            "created_at": report.created_at,
            "id": report.id,
            "note": report.note,
            "object_type": "user",
            "reported_by": user_1.serialize(user_1),
            "reported_comment": None,
            "reported_user": user_2.serialize(user_1),
            "reported_workout": None,
            "resolved": False,
            "resolved_at": None,
        }

    def test_it_returns_serialized_object_for_workout_report(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        workout_cycling_user_2.workout_visibility = PrivacyLevel.PUBLIC
        report = Report(
            note=self.random_string(),
            reported_by=user_1.id,
            reported_object=workout_cycling_user_2,
        )
        db.session.add(report)
        db.session.commit()

        serialized_report = report.serialize(user_1)

        assert serialized_report == {
            "created_at": report.created_at,
            "id": report.id,
            "note": report.note,
            "object_type": "workout",
            "reported_by": user_1.serialize(user_1),
            "reported_comment": None,
            "reported_user": user_2.serialize(),
            "reported_workout": workout_cycling_user_2.serialize(
                user_1, for_report=True
            ),
            "resolved": False,
            "resolved_at": None,
        }

    def test_it_returns_serialized_object_for_report_when_workout_is_not_visible(  # noqa
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        # in case visibility changed
        workout_cycling_user_2.workout_visibility = PrivacyLevel.PUBLIC
        report = Report(
            note=self.random_string(),
            reported_by=user_1.id,
            reported_object=workout_cycling_user_2,
        )
        db.session.add(report)
        workout_cycling_user_2.workout_visibility = PrivacyLevel.FOLLOWERS
        db.session.commit()

        serialized_report = report.serialize(user_1)

        assert serialized_report == {
            "created_at": report.created_at,
            "id": report.id,
            "note": report.note,
            "object_type": "workout",
            "reported_by": user_1.serialize(user_1),
            "reported_comment": None,
            "reported_user": user_2.serialize(),
            "reported_workout": '_WORKOUT_UNAVAILABLE_',
            "resolved": False,
            "resolved_at": None,
        }

    def test_it_returns_serialized_object_without_report_comments(
        self,
        app: Flask,
        user_1_admin: User,
        user_2: User,
        user_3: User,
    ) -> None:
        report = Report(
            note=self.random_string(),
            reported_by=user_2.id,
            reported_object=user_3,
        )
        db.session.add(report)
        db.session.flush()
        report_comment = ReportComment(
            report_id=report.id,
            user_id=user_1_admin.id,
            comment=self.random_string(),
        )
        db.session.add(report_comment)
        db.session.commit()

        serialized_report = report.serialize(user_2)

        assert serialized_report == {
            "created_at": report.created_at,
            "id": report.id,
            "note": report.note,
            "object_type": "user",
            "reported_by": user_2.serialize(user_2),
            "reported_comment": None,
            "reported_user": user_3.serialize(user_2),
            "reported_workout": None,
            "resolved": False,
            "resolved_at": None,
        }


class TestMinimalReportSerializerAsAdmin(CommentMixin, RandomMixin):
    def test_it_returns_serialized_comment_when_comment_is_not_visible(
        self,
        app: Flask,
        user_1_admin: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
        follow_request_from_user_3_to_user_2: FollowRequest,
    ) -> None:
        user_2.approves_follow_request_from(user_3)
        workout_cycling_user_2.workout_visibility = PrivacyLevel.FOLLOWERS
        comment = self.create_comment(
            user_3,
            workout_cycling_user_2,
            text_visibility=PrivacyLevel.FOLLOWERS,
        )
        report = Report(
            note=self.random_string(),
            reported_by=user_2.id,
            reported_object=comment,
        )
        db.session.add(report)
        db.session.commit()

        serialized_report = report.serialize(user_1_admin)

        assert serialized_report == {
            "created_at": report.created_at,
            "id": report.id,
            "note": report.note,
            "object_type": "comment",
            "reported_by": user_2.serialize(user_1_admin),
            "reported_comment": comment.serialize(
                user_1_admin, for_report=True
            ),
            "reported_user": user_3.serialize(),
            "reported_workout": None,
            "resolved": False,
            "resolved_at": None,
            "resolved_by": None,
            "updated_at": None,
        }

    def test_it_returns_serialized_workout_when_workout_is_not_visible(
        self,
        app: Flask,
        user_1_admin: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
        follow_request_from_user_3_to_user_2: FollowRequest,
    ) -> None:
        user_2.approves_follow_request_from(user_3)
        workout_cycling_user_2.workout_visibility = PrivacyLevel.FOLLOWERS
        report = Report(
            note=self.random_string(),
            reported_by=user_3.id,
            reported_object=workout_cycling_user_2,
        )
        db.session.add(report)
        db.session.commit()

        serialized_report = report.serialize(user_1_admin)

        assert serialized_report == {
            "created_at": report.created_at,
            "id": report.id,
            "note": report.note,
            "object_type": "workout",
            "reported_by": user_3.serialize(user_1_admin),
            "reported_comment": None,
            "reported_user": user_2.serialize(),
            "reported_workout": workout_cycling_user_2.serialize(
                user_1_admin, for_report=True
            ),
            "resolved": False,
            "resolved_at": None,
            "resolved_by": None,
            "updated_at": None,
        }

    def test_it_returns_serialized_object_when_no_report_comments(
        self,
        app: Flask,
        user_1_admin: User,
        user_2: User,
        user_3: User,
    ) -> None:
        report = Report(
            note=self.random_string(),
            reported_by=user_2.id,
            reported_object=user_3,
        )
        db.session.add(report)
        db.session.commit()

        serialized_report = report.serialize(user_1_admin)

        assert serialized_report == {
            "created_at": report.created_at,
            "id": report.id,
            "note": report.note,
            "object_type": "user",
            "reported_by": user_2.serialize(user_1_admin),
            "reported_comment": None,
            "reported_user": user_3.serialize(user_1_admin),
            "reported_workout": None,
            "resolved": False,
            "resolved_at": None,
            "resolved_by": None,
            "updated_at": None,
        }

    def test_it_does_not_return_serialized_object_with_report_comments_when_flag_is_false(  # noqa
        self,
        app: Flask,
        user_1_admin: User,
        user_2: User,
        user_3: User,
    ) -> None:
        report = Report(
            note=self.random_string(),
            reported_by=user_2.id,
            reported_object=user_3,
        )
        db.session.add(report)
        db.session.flush()
        report_comment = ReportComment(
            report_id=report.id,
            user_id=user_1_admin.id,
            comment=self.random_string(),
        )
        db.session.add(report_comment)
        db.session.commit()

        serialized_report = report.serialize(user_1_admin, full=False)

        assert serialized_report == {
            "created_at": report.created_at,
            "id": report.id,
            "note": report.note,
            "object_type": "user",
            "reported_by": user_2.serialize(user_1_admin),
            "reported_comment": None,
            "reported_user": user_3.serialize(user_1_admin),
            "reported_workout": None,
            "resolved": False,
            "resolved_at": None,
            "resolved_by": None,
            "updated_at": None,
        }

    def test_it_does_not_return_serialized_object_with_admin_actions_when_flag_is_false(  # noqa
        self,
        app: Flask,
        user_1_admin: User,
        user_2: User,
        user_3: User,
    ) -> None:
        report = Report(
            note=self.random_string(),
            reported_by=user_2.id,
            reported_object=user_3,
        )
        db.session.add(report)
        db.session.flush()
        admin_action = AdminAction(
            action_type="user_suspension",
            admin_user_id=user_1_admin.id,
            report_id=report.id,
            user_id=user_3.id,
        )
        db.session.add(admin_action)
        db.session.commit()

        serialized_report = report.serialize(user_1_admin, full=False)

        assert serialized_report == {
            "created_at": report.created_at,
            "id": report.id,
            "note": report.note,
            "object_type": "user",
            "reported_by": user_2.serialize(user_1_admin),
            "reported_comment": None,
            "reported_user": user_3.serialize(user_1_admin),
            "reported_workout": None,
            "resolved": False,
            "resolved_at": None,
            "resolved_by": None,
            "updated_at": None,
        }


class TestFullReportSerializerAsAdmin(CommentMixin, RandomMixin):
    def test_it_returns_serialized_object_with_report_comments(
        self,
        app: Flask,
        user_1_admin: User,
        user_2: User,
        user_3: User,
    ) -> None:
        report = Report(
            note=self.random_string(),
            reported_by=user_2.id,
            reported_object=user_3,
        )
        db.session.add(report)
        db.session.flush()
        report_comment = ReportComment(
            report_id=report.id,
            user_id=user_1_admin.id,
            comment=self.random_string(),
        )
        db.session.add(report_comment)
        db.session.commit()

        serialized_report = report.serialize(user_1_admin, full=True)

        assert serialized_report == {
            "admin_actions": [],
            "created_at": report.created_at,
            "comments": [report_comment.serialize(user_1_admin)],
            "id": report.id,
            "note": report.note,
            "object_type": "user",
            "reported_by": user_2.serialize(user_1_admin),
            "reported_comment": None,
            "reported_user": user_3.serialize(user_1_admin),
            "reported_workout": None,
            "resolved": False,
            "resolved_at": None,
            "resolved_by": None,
            "updated_at": None,
        }

    def test_it_returns_serialized_object_with_admin_actions(
        self,
        app: Flask,
        user_1_admin: User,
        user_2: User,
        user_3: User,
    ) -> None:
        report = Report(
            note=self.random_string(),
            reported_by=user_2.id,
            reported_object=user_3,
        )
        db.session.add(report)
        db.session.flush()
        admin_action_1 = AdminAction(
            action_type="user_suspension",
            admin_user_id=user_1_admin.id,
            report_id=report.id,
            user_id=user_3.id,
        )
        db.session.add(admin_action_1)
        admin_action_2 = AdminAction(
            action_type="report_resolution",
            admin_user_id=user_1_admin.id,
            report_id=report.id,
        )
        db.session.add(admin_action_2)
        db.session.commit()

        serialized_report = report.serialize(user_1_admin, full=True)

        assert serialized_report == {
            "admin_actions": [
                admin_action_1.serialize(user_1_admin),
                admin_action_2.serialize(user_1_admin),
            ],
            "created_at": report.created_at,
            "comments": [],
            "id": report.id,
            "note": report.note,
            "object_type": "user",
            "reported_by": user_2.serialize(user_1_admin),
            "reported_comment": None,
            "reported_user": user_3.serialize(user_1_admin),
            "reported_workout": None,
            "resolved": False,
            "resolved_at": None,
            "resolved_by": None,
            "updated_at": None,
        }


class ReportCommentTestCase(CommentMixin, UserModerationMixin):
    ...


class TestReportCommentModel(ReportCommentTestCase):
    def test_it_creates_comment_for_a_report(
        self, app: Flask, user_1_admin: User, user_2: User, user_3: User
    ) -> None:
        report = self.create_report(reporter=user_2, reported_object=user_3)
        created_at = datetime.now()
        comment = self.random_string()

        report_comment = ReportComment(
            report_id=report.id,
            user_id=user_1_admin.id,
            comment=comment,
            created_at=created_at,
        )
        db.session.add(report_comment)
        db.session.commit()

        assert report_comment.created_at == created_at
        assert report_comment.comment == comment
        assert report_comment.report_id == report.id
        assert report_comment.user_id == user_1_admin.id

    def test_it_creates_comment_for_a_report_without_date(
        self, app: Flask, user_1_admin: User, user_2: User, user_3: User
    ) -> None:
        report = self.create_report(reporter=user_2, reported_object=user_3)
        comment = self.random_string()
        now = datetime.utcnow()

        with freeze_time(now):
            report_comment = ReportComment(
                report_id=report.id,
                user_id=user_1_admin.id,
                comment=comment,
            )
        db.session.add(report_comment)
        db.session.commit()

        assert report_comment.created_at == now
        assert report_comment.comment == comment
        assert report_comment.report_id == report.id
        assert report_comment.user_id == user_1_admin.id


class TestReportCommentSerializer(ReportCommentTestCase):
    def test_it_raises_exception_when_user_has_no_admin_rights(
        self, app: Flask, user_1_admin: User, user_2: User, user_3: User
    ) -> None:
        report = self.create_report(reporter=user_2, reported_object=user_3)
        report_comment = ReportComment(
            report_id=report.id,
            user_id=user_1_admin.id,
            comment=self.random_string(),
        )

        with pytest.raises(ReportCommentForbiddenException):
            report_comment.serialize(user_2)

    def test_it_returns_serialized_report_comment(
        self, app: Flask, user_1_admin: User, user_2: User, user_3: User
    ) -> None:
        report = self.create_report(reporter=user_2, reported_object=user_3)
        comment = self.random_string()
        report_comment = ReportComment(
            report_id=report.id,
            user_id=user_1_admin.id,
            comment=comment,
        )
        db.session.add(report_comment)
        db.session.commit()

        serialized_comment = report_comment.serialize(user_1_admin)

        assert serialized_comment['created_at'] == report_comment.created_at
        assert serialized_comment['comment'] == report_comment.comment
        assert serialized_comment['id'] == report_comment.id
        assert serialized_comment['report_id'] == report.id
        assert serialized_comment['user'] == user_1_admin.serialize(
            user_1_admin
        )
