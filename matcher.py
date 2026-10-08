from models import User, UserSkill, UserWantsToLearn, ConnectionRequest, db
from sqlalchemy import or_

def find_mutual_matches(current_user_id):
    """
    Finds peer students for mutual skill exchange:
    - Peer has at least one verified skill that current_user wants to learn.
    - Current_user has at least one verified skill that peer wants to learn.
    - Enriches each match with:
      - skills_they_teach (what peer can teach current_user)
      - skills_you_teach (what current_user can teach peer)
      - connection_status ('connected', 'sent_pending', 'received_pending', 'none')
      - request_id (if pending from peer)
      - match_score (percentage affinity based on mutual overlap)
    """
    # 1. Fetch current user's verified skills & want-to-learn skills
    my_verified_skills = [
        s.skill_name for s in UserSkill.query.filter_by(user_id=current_user_id).all()
    ]
    my_want_skills = [
        s.skill_name for s in UserWantsToLearn.query.filter_by(user_id=current_user_id).all()
    ]

    if not my_verified_skills or not my_want_skills:
        return []

    # 2. Query candidates: other users who have skills in my_want_skills AND want skills in my_verified_skills
    candidate_users = db.session.query(User).filter(User.id != current_user_id).all()

    matches = []

    # Pre-fetch existing connections for current_user
    sent_requests = {
        req.to_user_id: req for req in ConnectionRequest.query.filter_by(from_user_id=current_user_id).all()
    }
    received_requests = {
        req.from_user_id: req for req in ConnectionRequest.query.filter_by(to_user_id=current_user_id).all()
    }

    for user in candidate_users:
        peer_verified = [
            s.skill_name for s in UserSkill.query.filter_by(user_id=user.id).all()
        ]
        peer_wants = [
            s.skill_name for s in UserWantsToLearn.query.filter_by(user_id=user.id).all()
        ]

        # Overlaps
        they_can_teach_me = [s for s in peer_verified if s in my_want_skills]
        i_can_teach_them = [s for s in my_verified_skills if s in peer_wants]

        if they_can_teach_me and i_can_teach_them:
            # Calculate match score based on Jaccard/overlap affinity
            total_unique_skills = len(set(my_want_skills + peer_wants + my_verified_skills + peer_verified))
            overlap_count = len(they_can_teach_me) + len(i_can_teach_them)
            # Base match score between 75% and 99%
            score = min(99, int(70 + (overlap_count / max(1, total_unique_skills)) * 30))

            # Determine connection status
            conn_status = 'none'
            req_id = None

            # Check if accepted
            if (user.id in sent_requests and sent_requests[user.id].status == 'accepted') or \
               (user.id in received_requests and received_requests[user.id].status == 'accepted'):
                conn_status = 'connected'
            elif user.id in sent_requests and sent_requests[user.id].status == 'pending':
                conn_status = 'sent_pending'
            elif user.id in received_requests and received_requests[user.id].status == 'pending':
                conn_status = 'received_pending'
                req_id = received_requests[user.id].id

            matches.append({
                'id': user.id,
                'name': user.name,
                'class': user.class_name,
                'gender': user.gender,
                'email': user.email,
                'phone': user.phone,
                'skill_rating': float(user.skill_rating or 0.0),
                'they_teach': they_can_teach_me,
                'you_teach': i_can_teach_them,
                'match_score': score,
                'connection_status': conn_status,
                'request_id': req_id
            })

    # Sort matches by match score descending
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    return matches


def get_accepted_connections(current_user_id):
    """
    Returns list of accepted connected peers with full contact details (email & phone).
    """
    connections = ConnectionRequest.query.filter(
        ((ConnectionRequest.from_user_id == current_user_id) | (ConnectionRequest.to_user_id == current_user_id)),
        ConnectionRequest.status == 'accepted'
    ).all()

    connected_users = []
    for conn in connections:
        peer_id = conn.to_user_id if conn.from_user_id == current_user_id else conn.from_user_id
        peer = db.session.get(User, peer_id)
        if peer:
            connected_users.append({
                'id': peer.id,
                'name': peer.name,
                'class': peer.class_name,
                'gender': peer.gender,
                'email': peer.email,
                'phone': peer.phone,
                'skill_rating': float(peer.skill_rating or 0.0)
            })
    return connected_users


def get_pending_received_requests(current_user_id):
    """
    Returns pending connection requests received by current user.
    """
    pending = ConnectionRequest.query.filter_by(
        to_user_id=current_user_id,
        status='pending'
    ).all()

    result = []
    for req in pending:
        sender = db.session.get(User, req.from_user_id)
        if sender:
            result.append({
                'request_id': req.id,
                'from_user_id': sender.id,
                'name': sender.name,
                'class': sender.class_name,
                'gender': sender.gender,
                'created_at': req.created_at
            })
    return result
