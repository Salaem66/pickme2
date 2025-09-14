-- Table pour stocker les notifications admin
CREATE TABLE IF NOT EXISTS admin_notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    message TEXT NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'info', -- info, success, warning, error
    target VARCHAR(20) NOT NULL DEFAULT 'all', -- all, authenticated, anonymous
    created_by UUID REFERENCES auth.users(id), -- ID de l'admin qui a envoyé
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Table pour stocker les abonnements push des utilisateurs
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, endpoint)
);

-- Table pour tracker les notifications reçues par utilisateur
CREATE TABLE IF NOT EXISTS notification_deliveries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    notification_id UUID REFERENCES admin_notifications(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    delivered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(notification_id, user_id)
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS admin_notifications_created_at_idx ON admin_notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS admin_notifications_active_idx ON admin_notifications(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS push_subscriptions_user_id_idx ON push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS push_subscriptions_active_idx ON push_subscriptions(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS notification_deliveries_user_id_idx ON notification_deliveries(user_id);
CREATE INDEX IF NOT EXISTS notification_deliveries_notification_id_idx ON notification_deliveries(notification_id);

-- RLS (Row Level Security)
ALTER TABLE admin_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_deliveries ENABLE ROW LEVEL SECURITY;

-- Politiques pour admin_notifications
CREATE POLICY "Admins can insert notifications" ON admin_notifications
    FOR INSERT WITH CHECK (auth.jwt() ->> 'email' = 'mael.sivenboren@gmail.com');

CREATE POLICY "Everyone can read active notifications" ON admin_notifications
    FOR SELECT USING (is_active = true);

CREATE POLICY "Admins can update notifications" ON admin_notifications
    FOR UPDATE USING (auth.jwt() ->> 'email' = 'mael.sivenboren@gmail.com');

-- Politiques pour push_subscriptions
CREATE POLICY "Users can manage their own subscriptions" ON push_subscriptions
    FOR ALL USING (auth.uid() = user_id);

-- Politiques pour notification_deliveries
CREATE POLICY "Users can view their own deliveries" ON notification_deliveries
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "System can insert deliveries" ON notification_deliveries
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update their own deliveries" ON notification_deliveries
    FOR UPDATE USING (auth.uid() = user_id);

-- Fonction pour nettoyer les anciennes notifications (optionnel)
CREATE OR REPLACE FUNCTION cleanup_old_notifications()
RETURNS void AS $$
BEGIN
    -- Désactiver les notifications de plus de 30 jours
    UPDATE admin_notifications
    SET is_active = false
    WHERE created_at < NOW() - INTERVAL '30 days' AND is_active = true;
END;
$$ LANGUAGE plpgsql;