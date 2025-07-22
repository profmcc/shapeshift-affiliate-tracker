package jwt_token_cache

import (
	"time"

	"github.com/pascaldekloe/jwt"
)

type CachedJwtToken struct {
	TokenType   string `json:"token_type"`
	ExpiresIn   int    `json:"expires_in"`
	AccessToken string `json:"access_token"`
}

func (t CachedJwtToken) IsExpired() bool {
	claims, err := jwt.ParseWithoutCheck([]byte(t.AccessToken))
	if err != nil {
		return false
	}

	isValid := claims.Valid(time.Now())
	return !isValid
}
